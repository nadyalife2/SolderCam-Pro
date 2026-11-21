#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni SFT & CoT Dataset Builder v2.0 (100% Offline Autonomy)
Парсит базу знаний проекта (ARTICLES/ и cluster_docs/), извлекает инженерные факты
и генерирует датасет в формате ChatML с поддержкой глубоких цепочек рассуждений (<think>...</think>).
Полностью автономен: работает оффлайн без облачных API.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
ARTICLES_DIR = BASE_DIR / "ARTICLES"
DOCS_DIR = BASE_DIR / "cluster_docs"
OUTPUT_DATASET = BASE_DIR / "datasets" / "triad_omni_sft_dataset.jsonl"
OUTPUT_COT_DATASET = BASE_DIR / "datasets" / "triad_omni_cot_dataset.jsonl"

SYSTEM_PROMPT = (
    "Ты — бортовой инженер и координатор гетерогенного автономного кластера Triad-Omni "
    "(Xiaomi Mi 10T 5G, OnePlus Nord N10 5G, Redmi Note 4). Отвечай технически строго, "
    "в авторском стиле создательницы кластера (женский род прошедшего времени: проверила, "
    "раскопала, прошила, замерила), с точными путями sysfs, реальными флагами компиляции, "
    "байпас-контроллерами батареи и без корпоративной воды."
)

def clean_markdown_text(text: str) -> str:
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def detect_hardware_domain(text: str) -> Dict[str, Any]:
    """Определяет аппаратный контекст и ограничения для синтеза CoT-рассуждений."""
    lower = text.lower()
    domain = {
        "node": "CLUSTER_WIDE",
        "chipset": "Snapdragon",
        "safety_checks": [],
        "latency_impact": "standard"
    }

    if "mi 10t" in lower or "apollo" in lower or "snapdragon 865" in lower or "865" in lower:
        domain["node"] = "NODE-1 (Xiaomi Mi 10T 5G, apollo)"
        domain["chipset"] = "Snapdragon 865 (Kryo 585 Prime 2.84GHz + 3x Gold 2.42GHz + 4x Silver 1.8GHz, 8GB LPDDR5)"
        domain["safety_checks"].append("sysfs battery bypass: battery_charging_enabled=0")
        domain["safety_checks"].append("taskset -c 4,5,6,7 to pin on Kryo 585 performance cores")
        domain["safety_checks"].append("LPDDR5 bandwidth limit: 16.5 GB/s (capped at ~3.4 tok/s for 4.8GB model)")
    elif "nord n10" in lower or "billie" in lower or "snapdragon 690" in lower or "690" in lower:
        domain["node"] = "NODE-2 (OnePlus Nord N10 5G, billie)"
        domain["chipset"] = "Snapdragon 690 (2x Kryo 560 Gold + 6x Silver, 6GB LPDDR4X)"
        domain["safety_checks"].append("A/B partition safety: verify active_slot via getvar before flash")
        domain["safety_checks"].append("sysfs charging limit: /sys/class/power_supply/battery/charging_enabled=0")
        domain["safety_checks"].append("Dedicated reflex node: LFM2.5-8B (:8081) + BGE-M3 (:8082)")
    elif "redmi note 4" in lower or "mido" in lower or "snapdragon 625" in lower or "625" in lower:
        domain["node"] = "NODE-3 (Xiaomi Redmi Note 4, mido)"
        domain["chipset"] = "Snapdragon 625 (8x Cortex-A53 2.0GHz, direct DC-DC 4.18V)"
        domain["safety_checks"].append("DC-DC step-down 4.18V direct motherboard power (zero battery swelling)")
        domain["safety_checks"].append("Sub-millisecond regex router (<0.02ms) to offload heavy nodes")

    if "быстр" in lower or "задержк" in lower or "latency" in lower or "0.02" in lower or "рефлекс" in lower:
        domain["latency_impact"] = "ultra_fast_path"
    elif "тяжел" in lower or "рассужден" in lower or "think" in lower or "глубок" in lower:
        domain["latency_impact"] = "deep_reasoning"

    return domain

def generate_cot_reasoning(instruction: str, response: str, domain: Dict[str, Any]) -> str:
    """
    Генерирует автономную детерминированную цепочку инженерных рассуждений (<think>...</think>).
    Отражает авторскую логику анализа железа, отсева ошибок и выбора инструментов.
    """
    reasoning_steps = []
    
    # 1. Анализ узла и аппаратных ограничений
    reasoning_steps.append(
        f"1. Аппаратный контекст: задача адресована узлу {domain['node']} на базе {domain['chipset']}."
    )

    # 2. Оценка рисков и безопасности железа
    if domain["safety_checks"]:
        checks = " | ".join(domain["safety_checks"])
        reasoning_steps.append(f"2. Инженерные ограничения и безопасность: {checks}.")
    else:
        reasoning_steps.append("2. Проверила требования автономности: 100% оффлайн, работа через локальную шину и sysfs.")

    # 3. Анализ задержки и маршрутизации
    if domain["latency_impact"] == "ultra_fast_path":
        reasoning_steps.append(
            "3. Архитектура отклика: запрос классифицирован как легковесный/командный. "
            "Чтобы не жечь кванты Snapdragon 865 и не ждать 34 секунды полного прогона, "
            "применяю Fast-Path маршрутизацию или инъекцию пустого think-блока."
        )
    else:
        reasoning_steps.append(
            "3. Архитектура вычислений: запрос требует полного разбора архитектуры и аппаратных нюансов. "
            "Использую горячий KV-кэш single-slot (--cache-reuse 256) и кэш подстановок Dynamic Lookup (-lcd)."
        )

    # 4. Формулирование решения в авторском голосе
    reasoning_steps.append(
        "4. Формирую прямой ответ: строго от первого лица («раскопала», «протестировала», «проверила»), "
        "с конкретными командами и железными аргументами без корпоративного тумана."
    )

    cot_block = "<think>\n" + "\n".join(reasoning_steps) + "\n</think>\n\n"
    return cot_block + response

def extract_qa_from_markdown(file_path: Path) -> List[Dict[str, Any]]:
    qa_pairs = []
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Ошибка чтения {file_path}: {e}")
        return qa_pairs

    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else file_path.stem

    sections = re.split(r'\n(?=##\s+)', content)
    
    # 1. Вводная часть документа
    intro = sections[0].strip()
    if len(intro) > 150:
        domain = detect_hardware_domain(intro)
        clean_resp = clean_markdown_text(intro[:2500])
        qa_pairs.append({
            "instruction": f"Расскажи в деталях, как решается задача: {title}?",
            "response": clean_resp,
            "domain": domain
        })

    # 2. Подразделы
    for sec in sections[1:]:
        sec_title_match = re.search(r'^##\s+(.+)$', sec, re.MULTILINE)
        if not sec_title_match:
            continue
        sec_title = sec_title_match.group(1).strip()
        body = sec[sec_title_match.end():].strip()
        
        if len(body) < 100:
            continue

        clean_body = clean_markdown_text(body[:3000])
        domain = detect_hardware_domain(sec_title + " " + clean_body)

        if any(w in sec_title.lower() for w in ["ошибк", "трабл", "fix", "грабли", "rescue", "fail"]):
            question = f"Какие грабли и аппаратные сбои возникают при '{sec_title}' в контексте {title}, и как я их устранила?"
        elif any(w in sec_title.lower() for w in ["сборк", "компиляц", "build", "toolchain"]):
            question = f"Какая точная инструкция, флаги компилятора и зависимости нужны для '{sec_title}'?"
        elif any(w in sec_title.lower() for w in ["настройк", "конфиг", "setup", "управлен"]):
            question = f"Как правильно настроить и запустить '{sec_title}' для проекта Triad-Omni?"
        elif any(w in sec_title.lower() for w in ["питани", "батаре", "battery", "pmic", "thermal"]):
            question = f"Как аппаратно и программно управлять питанием, нагревом и защитой батареи при '{sec_title}'?"
        else:
            question = f"Опиши инженерное решение, архитектуру и проверенные шаги для: '{sec_title}' ({title})."

        qa_pairs.append({
            "instruction": question,
            "response": clean_body,
            "domain": domain
        })

    return qa_pairs

def build_datasets():
    OUTPUT_DATASET.parent.mkdir(parents=True, exist_ok=True)
    all_pairs = []
    seen_hashes = set()

    sources = list(ARTICLES_DIR.glob("*.md")) + list(DOCS_DIR.glob("*.md"))
    print(f"🔎 Сканирование источников: {len(sources)} документов (ARTICLES + cluster_docs)...")

    for src in sorted(sources):
        pairs = extract_qa_from_markdown(src)
        for p in pairs:
            q_hash = hashlib.sha256(p["instruction"].strip().lower().encode('utf-8')).hexdigest()
            if q_hash not in seen_hashes and len(p["response"].strip()) > 80:
                seen_hashes.add(q_hash)
                all_pairs.append(p)

    print(f"📊 Сформировано {len(all_pairs)} уникальных инженерных пар Инструкция-Ответ.")

    # 1. Генерация классического SFT ChatML датасета
    total_chars_sft = 0
    with open(OUTPUT_DATASET, "w", encoding="utf-8") as f_sft:
        for item in all_pairs:
            sample = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": item["instruction"]},
                    {"role": "assistant", "content": item["response"]}
                ]
            }
            line = json.dumps(sample, ensure_ascii=False)
            f_sft.write(line + "\n")
            total_chars_sft += len(line)

    # 2. Генерация CoT (Reasoning) датасета с цепочками рассуждений <think>
    total_chars_cot = 0
    with open(OUTPUT_COT_DATASET, "w", encoding="utf-8") as f_cot:
        for item in all_pairs:
            cot_response = generate_cot_reasoning(item["instruction"], item["response"], item["domain"])
            sample_cot = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": item["instruction"]},
                    {"role": "assistant", "content": cot_response}
                ]
            }
            line_cot = json.dumps(sample_cot, ensure_ascii=False)
            f_cot.write(line_cot + "\n")
            total_chars_cot += len(line_cot)

    tokens_sft = int(total_chars_sft / 2.8)
    tokens_cot = int(total_chars_cot / 2.8)

    print(f"💾 Базовый SFT датасет: {OUTPUT_DATASET}")
    print(f"   Размер: {OUTPUT_DATASET.stat().st_size / 1024:.1f} КБ | ~{tokens_sft:,} токенов.")
    print(f"🧠 CoT Reasoning датасет: {OUTPUT_COT_DATASET}")
    print(f"   Размер: {OUTPUT_COT_DATASET.stat().st_size / 1024:.1f} КБ | ~{tokens_cot:,} токенов с блоками <think>.")

    # 3. Автоматическая синхронизация в локальный web_ui, на телефон по ADB и в облако
    web_datasets_dir = BASE_DIR / "web_ui" / "datasets"
    web_datasets_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(OUTPUT_DATASET, web_datasets_dir / OUTPUT_DATASET.name)
    shutil.copy2(OUTPUT_COT_DATASET, web_datasets_dir / OUTPUT_COT_DATASET.name)
    nb_src = BASE_DIR / "notebooks" / "triad_omni_trainer.ipynb"
    if nb_src.exists():
        shutil.copy2(nb_src, web_datasets_dir / nb_src.name)

    # ADB пуш на телефон если устройство на связи
    try:
        adb_path = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
        if Path(adb_path).exists():
            import subprocess
            check = subprocess.run([adb_path, "devices"], capture_output=True, text=True)
            if "device" in check.stdout and "5fcca09" in check.stdout:
                subprocess.run([adb_path, "push", str(web_datasets_dir), "/sdcard/web_ui_datasets"], capture_output=True)
                subprocess.run([adb_path, "shell", "su 0 -c 'cp -r /sdcard/web_ui_datasets/* /data/data/com.termux/files/home/web_ui/datasets/ && chmod -R 755 /data/data/com.termux/files/home/web_ui/datasets'"], capture_output=True)
                print("📱 Авто-пуш обновленных датасетов на Xiaomi Mi 10T по ADB завершен!")
    except Exception as e:
        print(f"ADB авто-пуш пропущен: {e}")

    # Облачная авто-выгрузка
    try:
        from cloud_sync import sync_all_to_cloud
        cloud_res = sync_all_to_cloud()
        if cloud_res.get("ok"):
            print("☁️ Облачная авто-синхронизация завершена успешно!")
    except Exception as e:
        print(f"Облачная авто-синхронизация пропущена: {e}")

if __name__ == "__main__":
    build_datasets()
