#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Manager & Versioning Engine for Triad-Omni.
Обеспечивает редактирование базы знаний без потери истории,
автоматические снепшоты в .history/, мгновенный переиндекс SQLite FTS5 RAG
и фиксацию правок для напоминаний об обновлении LoRA.
"""

import os
import re
import json
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
ARTICLES_DIR = BASE_DIR / "ARTICLES"
HISTORY_DIR = ARTICLES_DIR / ".history"
DB_PATH = BASE_DIR / "omni_knowledge.db"
CONFIG_DIR = BASE_DIR / "config"
META_FILE = CONFIG_DIR / "training_meta.json"

HISTORY_DIR.mkdir(parents=True, exist_ok=True)

def list_articles() -> List[Dict[str, Any]]:
    """Возвращает список всех статей с метаданными и количеством исторических версий"""
    results = []
    if not ARTICLES_DIR.exists():
        return results

    for f in sorted(ARTICLES_DIR.glob("*.md")):
        if f.name.startswith("."):
            continue
        stat = f.stat()
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
        
        # Читаем первую строку для заголовка
        title = f.stem.replace("_", " ")
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as af:
                for line in af:
                    line = line.strip()
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
        except Exception:
            pass

        # Считаем бэкапы этой статьи в .history/
        hist_count = len(list(HISTORY_DIR.glob(f"{f.stem}_*.md")))

        results.append({
            "filename": f.name,
            "stem": f.stem,
            "title": title,
            "size": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 1),
            "updated": mtime,
            "history_count": hist_count
        })
    return results

def get_article(filename: str) -> Optional[Dict[str, Any]]:
    """Возвращает текст статьи по имени файла"""
    safe_name = os.path.basename(filename)
    path = ARTICLES_DIR / safe_name
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        stat = path.stat()
        return {
            "filename": safe_name,
            "content": content,
            "size": stat.st_size,
            "updated": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
        }
    except Exception as e:
        return {"error": str(e)}

def save_article(filename: str, new_content: str) -> Dict[str, Any]:
    """
    Сохраняет статью:
    1. Делает копию текущей версии в .history/<stem>_<timestamp>.md
    2. Перезаписывает статью
    3. Мгновенно обновляет FTS5 в omni_knowledge.db
    4. Помечает в training_meta.json необходимость дообучения LoRA
    """
    safe_name = os.path.basename(filename)
    target = ARTICLES_DIR / safe_name

    # 1. Снепшот предыдущей версии
    if target.exists():
        old_text = target.read_text(encoding="utf-8", errors="replace")
        now_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        hist_file = HISTORY_DIR / f"{target.stem}_{now_ts}.md"
        hist_file.write_text(old_text, encoding="utf-8")

    # 2. Сохраняем новую версию
    target.write_text(new_content, encoding="utf-8")

    # 3. Мгновенный переиндекс в SQLite FTS5 (живой RAG)
    try:
        title = target.stem.replace("_", " ")
        for line in new_content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                break
        
        if DB_PATH.exists():
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Удаляем старую запись по названию если была
            c.execute("DELETE FROM articles_fts WHERE title = ?", (title,))
            # Вставляем актуальный текст
            c.execute("INSERT INTO articles_fts (title, content) VALUES (?, ?)", (title, new_content))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Warning: FTS5 update error: {e}")

    # 4. Обновляем мету обучения
    try:
        if META_FILE.exists():
            with open(META_FILE, "r", encoding="utf-8") as mf:
                meta = json.load(mf)
        else:
            meta = {}
        
        meta["needs_training"] = True
        meta["status_level"] = "warning"
        meta["status_text"] = "⚠️ Знания обновлены! Есть свежие правки для LoRA"
        meta["last_knowledge_edit_at"] = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        
        with open(META_FILE, "w", encoding="utf-8") as mf:
            json.dump(meta, mf, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return {
        "ok": True,
        "filename": safe_name,
        "message": f"Статья '{safe_name}' сохранена! Копия в .history, FTS5 RAG обновлён мгновенно."
    }

def get_article_history(filename: str) -> List[Dict[str, Any]]:
    """Возвращает список всех снепшотов для статьи"""
    safe_stem = Path(os.path.basename(filename)).stem
    versions = []
    for h in sorted(HISTORY_DIR.glob(f"{safe_stem}_*.md"), reverse=True):
        stat = h.stat()
        # Извлекаем таймстемп из имени: <stem>_YYYYMMDD_HHMMSS.md
        parts = h.stem.split("_")
        ts_str = "предыдущая"
        if len(parts) >= 2:
            try:
                date_part = parts[-2]
                time_part = parts[-1]
                ts_str = f"{date_part[6:8]}.{date_part[4:6]}.{date_part[0:4]} {time_part[0:2]}:{time_part[2:4]}"
            except Exception:
                pass
        
        versions.append({
            "backup_name": h.name,
            "created_at": ts_str,
            "size_kb": round(stat.st_size / 1024, 1)
        })
    return versions

def rollback_article(filename: str, backup_name: str) -> Dict[str, Any]:
    """Откатывает статью к выбранному историческому снепшоту"""
    safe_name = os.path.basename(filename)
    safe_backup = os.path.basename(backup_name)
    target = ARTICLES_DIR / safe_name
    backup_path = HISTORY_DIR / safe_backup

    if not backup_path.exists():
        return {"ok": False, "error": "Файл резервной копии не найден"}

    # Сохраняем текущее состояние перед откатом
    if target.exists():
        current_text = target.read_text(encoding="utf-8", errors="replace")
        now_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_roll = HISTORY_DIR / f"{target.stem}_pre_rollback_{now_ts}.md"
        pre_roll.write_text(current_text, encoding="utf-8")

    # Восстанавливаем из бэкапа
    restored_text = backup_path.read_text(encoding="utf-8", errors="replace")
    save_article(safe_name, restored_text)

    return {
        "ok": True,
        "message": f"Статья '{safe_name}' успешно откачена к версии {safe_backup}!"
    }

if __name__ == "__main__":
    arts = list_articles()
    print(f"Knowledge Manager готов! Найдено статей: {len(arts)}")
    if arts:
        print("Первая статья:", arts[0]["title"])
