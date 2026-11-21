#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
omni_harvester.py — Triad-Omni v4.9 Multi-Root Skill Harvester & Bundler
Сканирует манифесты SKILL.md во всех корнях, дедуплицирует по SHA-256 и приоритетам,
индексирует в SQLite FTS5 и собирает портативный бандл skills.omni.zip для кластера.
"""

import os
import re
import glob
import json
import time
import zipfile
import hashlib
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

DB_PATH = "skill_registry.db"
BUNDLE_PATH = "datasets/skills.omni.zip"

ROOT_SPECS = [
    # (kind, rel_or_abs_path, priority)
    ("project", os.path.join(".agents", "skills"), 100),
    ("project", os.path.join(".claude", "skills"), 100),
    ("project", os.path.join(".gemini", "skills"), 100),
    ("project", os.path.join(".cursor", "skills"), 100),
    ("omni", os.path.expanduser("~/.omni/skills"), 80),
    ("gemini-plugin", os.path.expanduser("~/.gemini/config/plugins"), 70),
    ("gemini-custom", os.path.expanduser("~/.gemini/config/skills"), 70),
    ("antigravity-builtin", os.path.expanduser("~/.gemini/antigravity/builtin/skills"), 30),
    ("claude-plugin", os.path.expanduser("~/.claude/plugins"), 65),
    ("cursor", os.path.expanduser("~/.cursor/skills"), 65),
]

FM_REGEX = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)

def init_db(conn: sqlite3.Connection):
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    # Проверяем схему, если старая — пересоздаем
    try:
        conn.execute("SELECT slug FROM skill_metadata LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("DROP TABLE IF EXISTS skill_metadata;")
        conn.execute("DROP TABLE IF EXISTS skills_fts;")
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skill_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL,
            name TEXT NOT NULL,
            version TEXT DEFAULT '1.0.0',
            kind TEXT NOT NULL,
            priority INTEGER NOT NULL,
            path TEXT NOT NULL UNIQUE,
            sha256 TEXT NOT NULL,
            mtime INTEGER NOT NULL,
            description TEXT,
            triggers TEXT,
            tools TEXT,
            status TEXT DEFAULT 'active'
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_slug ON skill_metadata(slug, priority DESC);")
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
            slug UNINDEXED,
            name,
            description,
            triggers,
            content='skill_metadata',
            content_rowid='id'
        );
    """)
    # Триггеры синхронизации FTS5
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS skill_ai AFTER INSERT ON skill_metadata BEGIN
            INSERT INTO skills_fts(rowid, slug, name, description, triggers)
            VALUES (new.id, new.slug, new.name, new.description, new.triggers);
        END;
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS skill_ad AFTER DELETE ON skill_metadata BEGIN
            INSERT INTO skills_fts(skills_fts, rowid, slug, name, description, triggers)
            VALUES ('delete', old.id, old.slug, old.name, old.description, old.triggers);
        END;
    """)
    conn.commit()

def parse_skill_file(fpath: str) -> Tuple[Dict, str]:
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return {}, ""
    
    m = FM_REGEX.match(content)
    if not m:
        name = os.path.basename(os.path.dirname(fpath))
        return {"name": name, "description": content[:300]}, content
    
    fm_raw = m.group(1)
    body = content[m.end():]
    meta = {}
    for line in fm_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line and not line.startswith("-"):
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if v.startswith("[") and v.endswith("]"):
                meta[k] = [x.strip(" '\"") for x in v[1:-1].split(",") if x.strip()]
            else:
                meta[k] = v
                
    if "name" not in meta:
        meta["name"] = os.path.basename(os.path.dirname(fpath))
    if "description" not in meta:
        meta["description"] = body.strip()[:300].replace("\n", " ")
        
    return meta, body

def scan_roots() -> Dict:
    t0 = time.perf_counter()
    os.makedirs(os.path.dirname(BUNDLE_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    
    cur = conn.cursor()
    known = {r[0]: (r[1], r[2]) for r in cur.execute("SELECT path, mtime, sha256 FROM skill_metadata").fetchall()}
    
    found_paths = set()
    stats = {"scanned": 0, "new": 0, "updated": 0, "unchanged": 0, "removed": 0}
    
    for kind, root_dir, prio in ROOT_SPECS:
        if not os.path.exists(root_dir):
            continue
        pattern = os.path.join(root_dir, "**", "SKILL.md")
        for fpath in glob.glob(pattern, recursive=True):
            stats["scanned"] += 1
            norm_path = os.path.abspath(fpath)
            found_paths.add(norm_path)
            
            try:
                mtime = int(os.path.getmtime(norm_path))
            except OSError:
                continue
                
            if norm_path in known and known[norm_path][0] == mtime:
                stats["unchanged"] += 1
                continue
                
            meta, body = parse_skill_file(norm_path)
            sha = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
            
            name = meta.get("name", os.path.basename(os.path.dirname(norm_path)))
            slug = re.sub(r'[^a-zA-Z0-9_\-]+', '-', name.lower()).strip('-')
            desc = meta.get("description", "")
            trig = json.dumps(meta.get("triggers", []), ensure_ascii=False)
            tools = json.dumps(meta.get("tools", []), ensure_ascii=False)
            
            # Экранируем описание для FTS5
            clean_desc = re.sub(r'[^\w\s]', ' ', desc)
            
            cur.execute("""
                INSERT INTO skill_metadata (slug, name, version, kind, priority, path, sha256, mtime, description, triggers, tools)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    name=excluded.name,
                    version=excluded.version,
                    priority=excluded.priority,
                    sha256=excluded.sha256,
                    mtime=excluded.mtime,
                    description=excluded.description,
                    triggers=excluded.triggers,
                    tools=excluded.tools
            """, (slug, name, meta.get("version", "1.0.0"), kind, prio, norm_path, sha, mtime, clean_desc, trig, tools))
            
            if norm_path in known:
                stats["updated"] += 1
            else:
                stats["new"] += 1

    # Удаляем файлы, которых больше нет
    for old_path in list(known.keys()):
        if old_path not in found_paths:
            cur.execute("DELETE FROM skill_metadata WHERE path = ?", (old_path,))
            stats["removed"] += 1
            
    # Дедупликация: активен скил с наивысшим приоритетом
    cur.execute("UPDATE skill_metadata SET status = 'shadowed'")
    cur.execute("""
        UPDATE skill_metadata
        SET status = 'active'
        WHERE id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY slug ORDER BY priority DESC, mtime DESC) as rn
                FROM skill_metadata
            ) WHERE rn = 1
        )
    """)
    conn.commit()
    conn.close()
    stats["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return stats

def create_bundle():
    """Собирает портативный skills.omni.zip (<2 МБ) для деплоя на Node-3 / Node-1"""
    t0 = time.perf_counter()
    scan_roots()
    
    with zipfile.ZipFile(BUNDLE_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(DB_PATH):
            zf.write(DB_PATH, arcname="skill_registry.db")
            
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT slug, path FROM skill_metadata WHERE status = 'active'")
        for slug, p in c.fetchall():
            if os.path.exists(p):
                zf.write(p, arcname=f"skills/{slug}/SKILL.md")
        conn.close()
        
    size_kb = round(os.path.getsize(BUNDLE_PATH) / 1024, 1)
    print(f"📦 Бандл собран: {BUNDLE_PATH} ({size_kb} КБ за {round((time.perf_counter() - t0)*1000, 1)} мс)")

if __name__ == "__main__":
    import sys
    if "--bundle" in sys.argv:
        create_bundle()
    else:
        res = scan_roots()
        print("🔍 Результаты сканирования скилов:", res)
