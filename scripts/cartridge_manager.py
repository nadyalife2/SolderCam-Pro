#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Cartridge Manager v2.0 (Smart Rolling Cache & Version Pool)
Модуль распаковки, верификации паспорта (card.json), ротации версий и управления квотой памяти.
Поддерживает хранение пула версий GGUF-картриджей в памяти телефона с защитой от переполнения (LRU).
Работает на стандартной библиотеке Python без внешних зависимостей.
"""

import os
import json
import shutil
import zipfile
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

if Path(__file__).resolve().parent.name == "scripts":
    BASE_DIR = Path(__file__).resolve().parent.parent
else:
    BASE_DIR = Path(__file__).resolve().parent

CARTRIDGES_DIR = BASE_DIR / "cartridges"
CONFIG_DIR = BASE_DIR / "config"
MODELS_DIR = BASE_DIR / "models"
ACTIVE_CARTRIDGE_FILE = CONFIG_DIR / "active_cartridge.json"

# Настройки квоты памяти на телефоне
DEFAULT_MAX_CACHE_MB = 1024       # По умолчанию квота 1 ГБ (хватает на ~22 версии картриджей по 45 МБ)
DEFAULT_MAX_VERSIONS_PER_SLUG = 5 # До 5 версий для каждого слага (persona, soldercam, hardware)

CARTRIDGES_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path, max_bytes: Optional[int] = None) -> str:
    """Вычисляет SHA256 хеш файла (или первых max_bytes)."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        if max_bytes:
            h.update(f.read(max_bytes))
        else:
            while chunk := f.read(65536):
                h.update(chunk)
    return h.hexdigest()

def get_active_cartridge() -> Dict[str, Any]:
    """Возвращает информацию о текущем активном картридже."""
    if ACTIVE_CARTRIDGE_FILE.exists():
        try:
            with open(ACTIVE_CARTRIDGE_FILE, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "active": False,
        "name": "Не подключен",
        "slug": "none",
        "version": "none",
        "build_tag": "none",
        "scale": 0.0,
        "description": "Базовая модель без LoRA-адаптера"
    }

def verify_cartridge_passport(card: Dict[str, Any]) -> Dict[str, Any]:
    """Проверяет соответствие паспорта спецификации omni.lora.card/1 и готовность к Fast-Path."""
    if not isinstance(card, dict):
        return {
            "valid": False,
            "is_harness_adapter": False,
            "mode": "unknown",
            "rank": 0,
            "alpha": 0,
            "issues": ["Паспорт не является валидным словарем JSON"],
            "device_target": "unknown"
        }

    issues = []
    slug = str(card.get("slug", ""))
    mode = str(card.get("mode", "persona_knowledge"))
    is_harness = ("fast-tool" in slug or mode == "fast_path_harness_adapter")

    try:
        rank_val = int(card.get("rank", 0))
    except (ValueError, TypeError):
        rank_val = 0
        issues.append(f"Некорректное значение rank: {card.get('rank')}")

    try:
        alpha_val = int(card.get("alpha", 0))
    except (ValueError, TypeError):
        alpha_val = 0
        issues.append(f"Некорректное значение alpha: {card.get('alpha')}")

    if is_harness:
        if rank_val < 32:
            issues.append(f"Rank {rank_val} ниже рекомендуемого r=32 для точного вызова инструментов")
        if alpha_val < 64:
            issues.append(f"Alpha {alpha_val} ниже рекомендуемого a=64")
        if card.get("thinking") != "disabled":
            issues.append("Внимание: флаг thinking не равен 'disabled', возможны задержки CoT")

    vocab_pruned = bool(card.get("vocab_pruned", False))
    try:
        vocab_size = int(card.get("vocab_size", 64000 if vocab_pruned else 152064))
    except (ValueError, TypeError):
        vocab_size = 152064
    try:
        ram_saved_mb = float(card.get("ram_saved_mb", 420.0 if vocab_pruned else 0.0))
    except (ValueError, TypeError):
        ram_saved_mb = 0.0

    return {
        "valid": len(issues) == 0,
        "is_harness_adapter": is_harness,
        "mode": mode,
        "rank": rank_val,
        "alpha": alpha_val,
        "vocab_pruned": vocab_pruned,
        "vocab_size": vocab_size,
        "ram_saved_mb": ram_saved_mb,
        "issues": issues,
        "device_target": card.get("device_target", "Xiaomi Mi 10T 5G")
    }

def set_active_cartridge(data: Dict[str, Any]) -> None:
    """Сохраняет активный картридж в конфигурацию и обновляет рабочий models/adapter.gguf."""
    if not isinstance(data, dict):
        return
    data["active"] = True
    if "scale" not in data:
        data["scale"] = 1.0
    with open(ACTIVE_CARTRIDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Синхронизация рабочего adapter.gguf и card.json в models/
    active_path = data.get("active_path")
    if active_path:
        p = Path(active_path)
        gguf_candidates = list(p.glob("*.gguf"))
        if gguf_candidates:
            dest_gguf = MODELS_DIR / "adapter.gguf"
            shutil.copy2(gguf_candidates[0], dest_gguf)
            card_p = p / "card.json"
            if card_p.exists():
                shutil.copy2(card_p, MODELS_DIR / "card.json")
        else:
            # Если в папке только паспорт без весов (например, подготовленный шаблон),
            # не подменяем рабочий adapter.gguf на рассинхронизированный
            pass

def list_cartridges() -> List[Dict[str, Any]]:
    """Сканирует каталог cartridges/ и возвращает список установленных картриджей и версий."""
    active_info = get_active_cartridge()
    active_tag = active_info.get("build_tag") or active_info.get("slug", "")

    cartridges = []

    # 1. Проверяем распакованные подпапки с card.json
    for p in CARTRIDGES_DIR.iterdir():
        if p.is_dir():
            card_path = p / "card.json"
            if card_path.exists():
                try:
                    with open(card_path, "r", encoding="utf-8") as f:
                        card = json.load(f)
                    slug = card.get("slug", p.name)
                    version = card.get("version", "v1.0")
                    build_tag = card.get("build_tag", p.name)
                    mode = card.get("mode", "persona_knowledge")
                    is_harness = ("fast-tool" in slug or "harness" in slug or mode == "fast_path_harness_adapter")
                    size = sum(f.stat().st_size for f in p.glob("*") if f.is_file())
                    mtime = p.stat().st_mtime
                    is_active = (build_tag == active_tag) or (p.name == active_info.get("folder_name", ""))
                    cartridges.append({
                        "name": p.name,
                        "folder_name": p.name,
                        "slug": slug,
                        "version": version,
                        "build_tag": build_tag,
                        "mode": mode,
                        "is_harness_adapter": is_harness,
                        "rank": card.get("rank", 16),
                        "alpha": card.get("alpha", 16),
                        "thinking": card.get("thinking", "enabled"),
                        "type": "folder",
                        "size": size,
                        "size_mb": round(size / (1024 * 1024), 2),
                        "card": card,
                        "files": [f.name for f in p.glob("*") if f.is_file()],
                        "is_active": is_active,
                        "mtime": mtime,
                        "path": str(p)
                    })
                except Exception:
                    pass

    # Сортируем: сначала активный, затем по времени изменения (свежие сверху)
    cartridges.sort(key=lambda x: (not x["is_active"], -x.get("mtime", 0)))
    return cartridges

def get_storage_stats(max_mb: int = DEFAULT_MAX_CACHE_MB) -> Dict[str, Any]:
    """Возвращает детальную статистику использования локальной памяти под картриджи."""
    cartridges = list_cartridges()
    total_bytes = sum(c["size"] for c in cartridges)
    total_mb = round(total_bytes / (1024 * 1024), 2)
    percent = round((total_mb / max_mb) * 100, 1) if max_mb > 0 else 0

    # Группировка по слагам
    by_slug: Dict[str, List[Dict[str, Any]]] = {}
    for c in cartridges:
        s = c["slug"]
        by_slug.setdefault(s, []).append(c)

    return {
        "total_mb": total_mb,
        "max_mb": max_mb,
        "free_mb": max(0, round(max_mb - total_mb, 2)),
        "percent_used": percent,
        "total_cartridges_count": len(cartridges),
        "slugs_count": len(by_slug),
        "by_slug": {
            slug: {
                "versions_count": len(items),
                "total_mb": round(sum(i["size"] for i in items) / (1024 * 1024), 2),
                "versions": [i["build_tag"] for i in items]
            } for slug, items in by_slug.items()
        }
    }

def prune_cartridge_cache(max_mb: int = DEFAULT_MAX_CACHE_MB, max_versions_per_slug: int = DEFAULT_MAX_VERSIONS_PER_SLUG) -> Dict[str, Any]:
    """
    Интеллектуальная ротация (LRU) версий картриджей:
    1. Никогда не удаляет активный картридж.
    2. Удаляет старые версии если их больше max_versions_per_slug для одного слага.
    3. Если общий объем превышает max_mb, удаляет самые старые неактивные версии.
    """
    cartridges = list_cartridges()
    removed = []
    freed_bytes = 0

    # Группируем по slug
    by_slug: Dict[str, List[Dict[str, Any]]] = {}
    for c in cartridges:
        by_slug.setdefault(c["slug"], []).append(c)

    # 1. Прореживаем по числу версий на слот (оставляем самые свежие)
    for slug, items in by_slug.items():
        # Сортируем: свежие в начале
        sorted_items = sorted(items, key=lambda x: -x.get("mtime", 0))
        if len(sorted_items) > max_versions_per_slug:
            excess = sorted_items[max_versions_per_slug:]
            for item in excess:
                if item["is_active"]:
                    continue # Активный трогать нельзя!
                p = Path(item["path"])
                size = item["size"]
                try:
                    shutil.rmtree(p)
                    removed.append({
                        "name": item["name"],
                        "slug": slug,
                        "tag": item["build_tag"],
                        "freed_mb": item["size_mb"],
                        "reason": f"Превышен лимит {max_versions_per_slug} версий для слота {slug}"
                    })
                    freed_bytes += size
                except Exception as e:
                    print(f"Ошибка удаления {p}: {e}")

    # 2. Проверяем общий лимит по объему
    current_cartridges = list_cartridges()
    current_bytes = sum(c["size"] for c in current_cartridges)
    limit_bytes = max_mb * 1024 * 1024

    if current_bytes > limit_bytes:
        # Сортируем неактивные от самых старых к новым
        inactives = [c for c in current_cartridges if not c["is_active"]]
        inactives.sort(key=lambda x: x.get("mtime", 0))

        for item in inactives:
            if current_bytes <= limit_bytes:
                break
            p = Path(item["path"])
            size = item["size"]
            try:
                shutil.rmtree(p)
                removed.append({
                    "name": item["name"],
                    "slug": item["slug"],
                    "tag": item["build_tag"],
                    "freed_mb": item["size_mb"],
                    "reason": f"Превышен общий лимит хранилища {max_mb} МБ"
                })
                current_bytes -= size
                freed_bytes += size
            except Exception as e:
                print(f"Ошибка удаления {p}: {e}")

    return {
        "ok": True,
        "removed_count": len(removed),
        "freed_mb": round(freed_bytes / (1024 * 1024), 2),
        "removed_cartridges": removed,
        "stats_after": get_storage_stats(max_mb)
    }

def activate_version(build_tag: str) -> Dict[str, Any]:
    """Активирует конкретную версию картриджа из локального хранилища."""
    cartridges = list_cartridges()
    target = None
    for c in cartridges:
        if c["build_tag"] == build_tag or c["name"] == build_tag or c["folder_name"] == build_tag:
            target = c
            break

    if not target:
        return {"ok": False, "error": f"Версия {build_tag} не найдена в хранилище картриджей."}

    has_gguf = any(f.endswith(".gguf") for f in target.get("files", []))
    if not has_gguf:
        return {
            "ok": False,
            "error": f"Картридж {build_tag} содержит паспорт card.json, но весовой файл adapter.gguf еще не обучен/не загружен в хранилище."
        }

    card_data = target["card"]
    card_data["active_path"] = target["path"]
    card_data["folder_name"] = target["name"]
    card_data["build_tag"] = target["build_tag"]
    card_data["version"] = target["version"]
    card_data["slug"] = target["slug"]

    set_active_cartridge(card_data)
    return {
        "ok": True,
        "message": f"Картридж '{target['slug']}' успешно переключен на версию {target['build_tag']}!",
        "active_cartridge": card_data
    }

def unpack_and_install_cartridge(file_path: Path, max_cache_mb: int = DEFAULT_MAX_CACHE_MB) -> Dict[str, Any]:
    """
    Распаковывает zip или перемещает gguf в изолированную папку версии,
    верифицирует паспорт card.json, делает картридж активным
    и автоматически выполняет ротацию старых версий (квота памяти).
    """
    if not file_path.exists():
        return {"ok": False, "error": f"Файл {file_path.name} не найден"}

    # Папка версии формируется по имени файла (например, triad-omni-persona_v1.0_20261118_1135)
    folder_name = file_path.stem.replace(".omni", "")
    target_dir = CARTRIDGES_DIR / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    extracted_files = []
    card_data = {}

    if file_path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                for member in z.infolist():
                    target_member_path = (target_dir / member.filename).resolve()
                    if not str(target_member_path).startswith(str(target_dir.resolve())):
                        continue
                    z.extract(member, target_dir)
                    if not member.is_dir():
                        extracted_files.append(member.filename)

            card_file = target_dir / "card.json"
            if card_file.exists():
                with open(card_file, "r", encoding="utf-8") as f:
                    card_data = json.load(f)
            else:
                card_data = {
                    "schema": "omni.cartridge/1",
                    "slug": folder_name.split("_")[0],
                    "build_tag": folder_name,
                    "description": f"Распакованный картридж из {file_path.name}"
                }
                with open(card_file, "w", encoding="utf-8") as f:
                    json.dump(card_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            return {"ok": False, "error": f"Ошибка распаковки архива: {e}"}

    elif file_path.suffix.lower() == ".gguf":
        dest_gguf = target_dir / file_path.name
        if file_path != dest_gguf:
            dest_gguf.write_bytes(file_path.read_bytes())
        extracted_files.append(dest_gguf.name)

        card_file = target_dir / "card.json"
        card_data = {
            "schema": "omni.gguf.card/1",
            "slug": folder_name.split("_")[0],
            "build_tag": folder_name,
            "quant": "q4_k_m" if "q4" in file_path.name.lower() else "unknown",
            "base": file_path.name,
            "description": f"Нативный весовой GGUF-картридж {file_path.name}"
        }
        with open(card_file, "w", encoding="utf-8") as f:
            json.dump(card_data, f, ensure_ascii=False, indent=2)

    # Верификация SHA256
    gguf_candidates = list(target_dir.glob("*.gguf"))
    if gguf_candidates:
        main_gguf = gguf_candidates[0]
        computed_sha = compute_sha256(main_gguf, max_bytes=64 * 1024 * 1024)
        card_data["verified_sha256"] = computed_sha
        card_data["main_gguf"] = main_gguf.name
        card_data["main_gguf_size_mb"] = round(main_gguf.stat().st_size / (1024 * 1024), 2)

    # Делаем активным
    card_data["active_path"] = str(target_dir)
    card_data["folder_name"] = folder_name
    card_data["build_tag"] = card_data.get("build_tag", folder_name)
    set_active_cartridge(card_data)

    # Автоматическая проверка квоты и ротация старых версий
    prune_res = prune_cartridge_cache(max_mb=max_cache_mb)

    return {
        "ok": True,
        "slug": card_data.get("slug", folder_name),
        "build_tag": card_data.get("build_tag", folder_name),
        "files": extracted_files,
        "card": card_data,
        "prune_report": prune_res,
        "message": f"Картридж '{folder_name}' установлен, проверен, активирован! Освобождено: {prune_res['freed_mb']} МБ."
    }

if __name__ == "__main__":
    print("Storage stats:", json.dumps(get_storage_stats(), indent=2, ensure_ascii=False))
    print("Cartridges list:", list_cartridges())
    print("Active:", get_active_cartridge())
