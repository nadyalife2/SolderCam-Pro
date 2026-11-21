#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест мульти-источникового сборщика и динамического FTS5 роутера скилов.
"""
import os
import glob
import sqlite3
import time
import re
from typing import List, Dict

DB_PATH = "skill_registry.db"

ROOTS = [
    os.path.join(os.getcwd(), ".agents", "skills"),
    os.path.expanduser("~/.gemini/antigravity/builtin/skills"),
    os.path.expanduser("~/.gemini/config/skills"),
    os.path.expanduser("~/.gemini/config/plugins"),
    os.path.expanduser("~/.claude/plugins"),
    os.path.expanduser("~/.cursor/skills"),
]

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS skills_fts;")
        conn.execute("DROP TABLE IF EXISTS skill_metadata;")
        conn.execute("""
            CREATE VIRTUAL TABLE skills_fts USING fts5(
                skill_id UNINDEXED,
                name,
                description,
                path
            );
        """)
        conn.execute("""
            CREATE TABLE skill_metadata (
                skill_id TEXT PRIMARY KEY,
                name TEXT,
                path TEXT,
                description TEXT
            );
        """)
        conn.commit()

def parse_skill_md(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None, None
    
    # Парсим YAML frontmatter
    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    name = None
    desc = ""
    if fm_match:
        fm = fm_match.group(1)
        name_match = re.search(r"^name:\s*([^\n]+)", fm, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip().strip("'\"")
        desc_match = re.search(r"^description:\s*([^\n]+)", fm, re.MULTILINE)
        if desc_match:
            desc = desc_match.group(1).strip().strip("'\"")
            
    if not name:
        name = os.path.basename(os.path.dirname(file_path))
    if not desc:
        desc = content[:400].replace("\n", " ")
        
    return name, desc

def harvest():
    init_db()
    found = 0
    with sqlite3.connect(DB_PATH) as conn:
        for root in ROOTS:
            if not os.path.exists(root):
                continue
            pattern = os.path.join(root, "**", "SKILL.md")
            for fpath in glob.glob(pattern, recursive=True):
                name, desc = parse_skill_md(fpath)
                if not name:
                    continue
                skill_id = name.lower()
                clean_desc = re.sub(r'[^\w\s]', ' ', desc)
                conn.execute("""
                    INSERT INTO skills_fts(skill_id, name, description, path)
                    VALUES (?, ?, ?, ?)
                """, (skill_id, name, clean_desc, fpath))
                conn.execute("""
                    INSERT OR REPLACE INTO skill_metadata(skill_id, name, path, description)
                    VALUES (?, ?, ?, ?)
                """, (skill_id, name, fpath, desc))
                found += 1
        conn.commit()
    return found

def select_skills(query: str, top_k: int = 2) -> List[Dict]:
    t0 = time.perf_counter()
    clean_q = re.sub(r'[^\w\s]', ' ', query)
    words = [w for w in clean_q.split() if len(w) > 2]
    if not words:
        return []
    terms = " OR ".join(f'"{w}"' for w in words)
    
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT SF.skill_id, SF.name, SF.path, MIN(rank) as best_rank
            FROM skills_fts SF
            WHERE skills_fts MATCH ?
            GROUP BY SF.skill_id
            ORDER BY best_rank
            LIMIT ?
        """, (terms, top_k))
        rows = c.fetchall()
        
    dt_ms = (time.perf_counter() - t0) * 1000
    res = []
    for r in rows:
        res.append({"id": r[0], "name": r[1], "path": r[2], "rank": r[3], "latency_ms": dt_ms})
    return res

if __name__ == "__main__":
    count = harvest()
    print(f"Собрано {count} скилов во всех корнях!")
    for q in [
        "как настроить камеру и ntc термистор",
        "хочу запустить llama.cpp на termux мобильном процессоре",
        "как снять фейк характеристики с планшета и сделать speed компиляцию",
        "декомпиляция apk и реверс машинного кода"
    ]:
        matches = select_skills(q, top_k=2)
        print(f"\nЗапрос: '{q}'")
        for m in matches:
            print(f"  -> Найдено: [{m['name']}] (задержка: {m['latency_ms']:.2f} мс) путь: {m['path']}")
