#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Cloud Sync Engine v1.0
Управляет выгрузкой датасетов и ноутбуков в облачные хранилища (Яндекс.Диск, Google Drive).
- Поддерживает REST API Яндекс.Диска (загрузка + публикация прямых ссылок).
- Поддерживает авто-копирование в локальные папки десктопных клиентов Яндекс.Диск и Google Drive.
- Хранит ссылки на публичные облачные папки для 1-клик перехода из интерфейса.
- Поддерживает автоматический хук при пересборке датасетов.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import shutil
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "cloud_config.json"
DATASETS_DIR = BASE_DIR / "datasets"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
WEB_UI_DATASETS = BASE_DIR / "web_ui" / "datasets"

DEFAULT_CONFIG = {
    "yandex_disk_url": "https://disk.yandex.ru/",
    "google_drive_url": "https://drive.google.com/",
    "yandex_token": "",
    "auto_upload_on_update": True,
    "last_sync_time": "Никогда",
    "last_status": "Ожидает настройки"
}

def load_cloud_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_cloud_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Дополняем недостающие ключи
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception as e:
        print(f"Ошибка чтения {CONFIG_FILE}: {e}")
        return DEFAULT_CONFIG.copy()

def save_cloud_config(cfg: dict) -> bool:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения {CONFIG_FILE}: {e}")
        return False

def find_local_cloud_folders() -> dict:
    """Ищет локально синхронизируемые папки облачных дисков на ПК пользователя."""
    home = Path.home()
    candidates = {
        "yandex": [
            home / "YandexDisk",
            home / "Yandex.Disk",
            Path("C:/YandexDisk"),
            Path("D:/YandexDisk")
        ],
        "gdrive": [
            home / "Google Drive",
            home / "GoogleДиск",
            Path("G:/Мой диск"),
            Path("G:/My Drive")
        ]
    }
    found = {}
    for service, paths in candidates.items():
        for p in paths:
            if p.exists() and p.is_dir():
                found[service] = p
                break
    return found

def get_yandex_public_download_url(public_url_or_key: str, file_path: str = None) -> dict:
    """
    Получает прямую ссылку на скачивание файла из публичной ссылки Яндекс.Диска без токена и авторизации!
    Работает через официальный открытый API: /v1/disk/public/resources/download
    """
    try:
        api_url = f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={urllib.parse.quote(public_url_or_key)}"
        if file_path:
            api_url += f"&path={urllib.parse.quote(file_path)}"
        req = urllib.request.Request(api_url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {"ok": True, "download_url": data.get("href")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def upload_file_to_yandex_disk(token: str, local_path: Path, remote_folder: str = "Triad-Omni") -> dict:
    """Загружает файл на Яндекс.Диск через официальный REST API с последующей публикацией."""
    if not token or not token.strip():
        return {"ok": False, "error": "Токен Яндекс.Диска не указан"}
    if not local_path.exists():
        return {"ok": False, "error": f"Локальный файл не найден: {local_path}"}

    headers = {"Authorization": f"OAuth {token.strip()}"}

    # 1. Создаем папку если нужно
    try:
        mkdir_url = f"https://cloud-api.yandex.net/v1/disk/resources?path={urllib.parse.quote(remote_folder)}"
        req = urllib.request.Request(mkdir_url, headers=headers, method="PUT")
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        if e.code != 409: # 409 значит папка уже существует
            pass
    except Exception:
        pass

    remote_path = f"{remote_folder}/{local_path.name}"

    # 2. Получаем ссылку на загрузку
    try:
        get_url = f"https://cloud-api.yandex.net/v1/disk/resources/upload?path={urllib.parse.quote(remote_path)}&overwrite=true"
        req = urllib.request.Request(get_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            upload_href = data.get("href")
    except Exception as e:
        return {"ok": False, "error": f"Не удалось получить URL загрузки: {e}"}

    # 3. Загружаем файл
    try:
        with open(local_path, "rb") as f_data:
            req_upload = urllib.request.Request(upload_href, data=f_data.read(), method="PUT")
            with urllib.request.urlopen(req_upload, timeout=60) as resp_upload:
                if resp_upload.status not in (200, 201, 202):
                    return {"ok": False, "error": f"Ошибка PUT: HTTP {resp_upload.status}"}
    except Exception as e:
        return {"ok": False, "error": f"Ошибка передачи байтов: {e}"}

    # 4. Публикуем для получения постоянной ссылки
    public_url = ""
    try:
        pub_url = f"https://cloud-api.yandex.net/v1/disk/resources/publish?path={urllib.parse.quote(remote_path)}"
        req_pub = urllib.request.Request(pub_url, headers=headers, method="PUT")
        urllib.request.urlopen(req_pub, timeout=5)

        info_url = f"https://cloud-api.yandex.net/v1/disk/resources?path={urllib.parse.quote(remote_path)}"
        req_info = urllib.request.Request(info_url, headers=headers)
        with urllib.request.urlopen(req_info, timeout=5) as resp_info:
            info_data = json.loads(resp_info.read().decode())
            public_url = info_data.get("public_url", "")
    except Exception:
        pass

    return {"ok": True, "remote_path": remote_path, "public_url": public_url}

def sync_all_to_cloud(user_token: str = None) -> dict:
    """
    Выполняет полную синхронизацию всех файлов обучения:
    1. Проверяет наличие triad_omni_sft_dataset.jsonl, triad_omni_cot_dataset.jsonl, triad_omni_trainer.ipynb.
    2. Копирует в локальные облачные папки (если есть).
    3. Выгружает на Яндекс.Диск через REST API (если токен задан).
    """
    cfg = load_cloud_config()
    token = user_token or cfg.get("yandex_token", "")

    files_to_sync = [
        DATASETS_DIR / "triad_omni_sft_dataset.jsonl",
        DATASETS_DIR / "triad_omni_cot_dataset.jsonl",
        NOTEBOOKS_DIR / "triad_omni_trainer.ipynb"
    ]

    results = {"copied_local": [], "uploaded_yandex": [], "errors": []}

    # 1. Локальные папки облачных дисков
    local_folders = find_local_cloud_folders()
    for service, path in local_folders.items():
        dest_dir = path / "Triad-Omni"
        dest_dir.mkdir(parents=True, exist_ok=True)
        for f in files_to_sync:
            if f.exists():
                try:
                    shutil.copy2(f, dest_dir / f.name)
                    results["copied_local"].append(f"{service}: {f.name}")
                except Exception as e:
                    results["errors"].append(f"Копирование в {service}: {e}")

    # 2. REST API Яндекс.Диска
    yandex_public_urls = {}
    if token and token.strip():
        for f in files_to_sync:
            if f.exists():
                res = upload_file_to_yandex_disk(token, f)
                if res.get("ok"):
                    results["uploaded_yandex"].append(f.name)
                    if res.get("public_url"):
                        yandex_public_urls[f.name] = res["public_url"]
                else:
                    results["errors"].append(f"Яндекс.Диск {f.name}: {res.get('error')}")

    now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    cfg["last_sync_time"] = now_str

    if results["uploaded_yandex"]:
        cfg["last_status"] = f"🟢 Выгружено на Яндекс.Диск: {len(results['uploaded_yandex'])} файлов"
        # Если была получена публичная ссылка на SFT датасет или папку, обновляем URL
        if "triad_omni_sft_dataset.jsonl" in yandex_public_urls:
            cfg["yandex_disk_url"] = yandex_public_urls["triad_omni_sft_dataset.jsonl"]
    elif results["copied_local"]:
        cfg["last_status"] = f"🟢 Скопировано в локальные папки: {', '.join(results['copied_local'])}"
    else:
        if not token:
            cfg["last_status"] = "ℹ️ Токен не задан. Используются прямые ссылки на облако"
        else:
            cfg["last_status"] = "⚠️ Ошибка синхронизации (см. логи)"

    save_cloud_config(cfg)
    return {
        "ok": len(results["errors"]) == 0 or len(results["uploaded_yandex"]) > 0 or len(results["copied_local"]) > 0,
        "results": results,
        "config": cfg
    }

if __name__ == "__main__":
    print("☁️ Запуск проверки облачной синхронизации Triad-Omni...")
    status = sync_all_to_cloud()
    print(json.dumps(status, ensure_ascii=False, indent=2))
