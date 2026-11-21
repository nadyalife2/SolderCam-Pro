#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль отслеживания статуса обучения LoRA в кластере Triad-Omni.
Управляет датами, количеством сэмплов и формирует напоминания об обучении.
"""

import os
import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
META_FILE = CONFIG_DIR / "training_meta.json"
DATASET_FILE = BASE_DIR / "datasets" / "triad_omni_sft_dataset.jsonl"
NOTEBOOK_FILE = BASE_DIR / "notebooks" / "triad_omni_trainer.ipynb"
RAW_DOCS_DIR = BASE_DIR / "raw_docs"
ARTICLES_DIR = BASE_DIR / "ARTICLES"
CARTRIDGES_DIR = BASE_DIR / "cartridges"

def get_current_samples_count() -> int:
    if not DATASET_FILE.exists():
        return 0
    try:
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0

def get_raw_docs_count() -> int:
    if not RAW_DOCS_DIR.exists():
        return 0
    return len([f for f in RAW_DOCS_DIR.glob("**/*.*") if f.is_file() and f.name != "README.md"])

def get_articles_count() -> int:
    if not ARTICLES_DIR.exists():
        return 0
    return len(list(ARTICLES_DIR.glob("*.md")))

def load_training_state() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not META_FILE.exists():
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        curr = get_current_samples_count()
        state = {
            "last_trained_at": now,
            "last_trained_human": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "trained_samples_count": curr,
            "recommended_interval_days": 7
        }
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    else:
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}

    curr_samples = get_current_samples_count()
    trained_samples = state.get("trained_samples_count", 0)
    diff_samples = max(0, curr_samples - trained_samples)

    # Вычисляем сколько дней прошло
    last_str = state.get("last_trained_at", "")
    days_passed = 0
    if last_str:
        try:
            last_dt = datetime.datetime.fromisoformat(last_str.replace("Z", ""))
            days_passed = (datetime.datetime.now() - last_dt).days
        except Exception:
            days_passed = 0

    interval = state.get("recommended_interval_days", 7)
    raw_count = get_raw_docs_count()
    art_count = get_articles_count()

    # Пора обучать если: появилось >= 10 новых сэмплов, или прошло > 7 дней, или модель еще ни разу не обучалась
    needs_training = (diff_samples >= 10) or (days_passed >= interval) or (trained_samples == 0)

    if needs_training:
        if diff_samples > 0:
            status_text = f"⚠️ Пора обновить LoRA: +{diff_samples} новых сэмплов!"
        else:
            status_text = f"⚠️ Пора обновить LoRA: прошло {days_passed} дн. с прошлого обучения"
        status_level = "warning"
    else:
        status_text = f"🟢 Модель актуальна (обучена {state.get('last_trained_human', 'недавно')}, {trained_samples} сэмплов)"
        status_level = "ok"

    # Собираем список файлов обучения
    files_list = []
    if DATASET_FILE.exists():
        stat = DATASET_FILE.stat()
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
        files_list.append({
            "name": "triad_omni_sft_dataset.jsonl",
            "type": "dataset",
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "updated": mtime,
            "desc": f"SFT-датасет ChatML ({curr_samples} Q&A пар)",
            "download_url": "/api/dataset/download"
        })

    if NOTEBOOK_FILE.exists():
        stat = NOTEBOOK_FILE.stat()
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
        files_list.append({
            "name": "triad_omni_trainer.ipynb",
            "type": "notebook",
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "updated": mtime,
            "desc": "Jupyter Notebook для Google Colab (Tesla T4 GPU)",
            "download_url": "/api/training/notebook/download",
            "colab_url": "https://colab.research.google.com"
        })

    cartridges = list(CARTRIDGES_DIR.glob("*.zip")) + list(CARTRIDGES_DIR.glob("*.gguf"))
    for c in cartridges:
        stat = c.stat()
        files_list.append({
            "name": c.name,
            "type": "cartridge",
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "updated": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
            "desc": "Готовый LoRA-адаптер для Node-1 (Xiaomi Mi 10T)",
            "download_url": f"/api/cartridges/download?file={c.name}"
        })

    return {
        "needs_training": needs_training,
        "status_level": status_level,
        "status_text": status_text,
        "last_trained_at": state.get("last_trained_at", ""),
        "last_trained_human": state.get("last_trained_human", "16.11.2026 22:50"),
        "days_passed": days_passed,
        "trained_samples": trained_samples,
        "current_samples": curr_samples,
        "diff_samples": diff_samples,
        "raw_docs_count": raw_count,
        "articles_count": art_count,
        "files": files_list
    }

def mark_as_trained() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    now_dt = datetime.datetime.now()
    curr_samples = get_current_samples_count()
    state = {
        "last_trained_at": now_dt.isoformat(),
        "last_trained_human": now_dt.strftime("%d.%m.%Y %H:%M"),
        "trained_samples_count": curr_samples,
        "recommended_interval_days": 7
    }
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return load_training_state()

if __name__ == "__main__":
    st = load_training_state()
    print("Training State:", json.dumps(st, ensure_ascii=False, indent=2))
