#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Sovereign Offline Knowledge Base Builder
Индексирует все статьи из ARTICLES/ и cluster_docs/ в локальную базу SQLite FTS5.
База весит всего ~1.5 МБ, копируется на смартфоны и обеспечивает поиск за 1-3 миллисекунды
без интернета и без облаков.
"""

import os
import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARTICLES_DIR = BASE_DIR / "ARTICLES"
DOCS_DIR = BASE_DIR / "cluster_docs"
OUTPUT_DB = BASE_DIR / "datasets" / "omni_knowledge.db"

def build_fts_db():
    OUTPUT_DB.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_DB.exists():
        OUTPUT_DB.unlink()

    conn = sqlite3.connect(OUTPUT_DB)
    c = conn.cursor()

    c.execute("PRAGMA journal_mode = WAL;")
    c.execute("PRAGMA synchronous = NORMAL;")
    c.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        title TEXT,
        content TEXT
    );
    """)
    c.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
        title, content, content='articles', content_rowid='id'
    );
    """)

    sources = list(ARTICLES_DIR.glob("*.md")) + list(DOCS_DIR.glob("*.md"))
    print(f"📚 Сканирование и индексация {len(sources)} документов...")

    indexed_count = 0
    for src in sources:
        try:
            text = src.read_text(encoding='utf-8')
            title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else src.stem
            
            c.execute("INSERT INTO articles (filename, title, content) VALUES (?, ?, ?)",
                      (src.name, title, text))
            rowid = c.lastrowid
            c.execute("INSERT INTO articles_fts (rowid, title, content) VALUES (?, ?, ?)",
                      (rowid, title, text))
            indexed_count += 1
        except Exception as e:
            print(f"Ошибка чтения {src}: {e}")

    conn.commit()
    conn.close()

    print(f"✅ База знаний успешно создана: {OUTPUT_DB}")
    print(f"📊 Проиндексировано: {indexed_count} статей | Размер: {OUTPUT_DB.stat().st_size / 1024:.1f} КБ")

if __name__ == "__main__":
    build_fts_db()
