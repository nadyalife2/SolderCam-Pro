#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Raw Knowledge Ingestion Pipeline
Автоматически обрабатывает PDF, посты, заметки и HTML из raw_docs/,
преобразует их в структурированный Markdown и помещает в cluster_docs/,
после чего сразу обновляет локальную SQLite FTS5 базу знаний omni_knowledge.db.
"""

import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw_docs"
DOCS_DIR = BASE_DIR / "cluster_docs"
SCRIPTS_DIR = BASE_DIR / "scripts"

PDF_DIR = RAW_DIR / "pdf"
POSTS_DIR = RAW_DIR / "posts"
NOTES_DIR = RAW_DIR / "notes"

# Создаем папки если их нет
for p in [PDF_DIR, POSTS_DIR, NOTES_DIR, DOCS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Извлекает текст из PDF файла"""
    text = ""
    # Попытка 1: через pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        for i, page in enumerate(reader.pages):
            p_text = page.extract_text() or ""
            text += f"\n\n### Страница {i+1}\n\n" + p_text
        if text.strip():
            return text
    except ImportError:
        pass
    except Exception as e:
        print(f"pypdf ошибка для {pdf_path.name}: {e}")

    # Попытка 2: через pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                p_text = page.extract_text() or ""
                text += f"\n\n### Страница {i+1}\n\n" + p_text
        if text.strip():
            return text
    except ImportError:
        pass
    except Exception as e:
        print(f"pdfplumber ошибка для {pdf_path.name}: {e}")

    # Попытка 3: через PyPDF2
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages):
                text += f"\n\n### Страница {i+1}\n\n" + (page.extract_text() or "")
        if text.strip():
            return text
    except Exception as e:
        print(f"PyPDF2 ошибка для {pdf_path.name}: {e}")

    if not text.strip():
        print(f"⚠️ Не удалось извлечь текст из {pdf_path.name}. Установите pypdf: pip install pypdf")
    return text

def clean_html(raw_html: str) -> str:
    """Очищает HTML теги и оставляет читаемый текст"""
    # Удаляем скрипты и стили
    text = re.sub(r'<script.*?</script>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Превращаем заголовки h1..h4 в markdown #..####
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', r'\n', text, flags=re.IGNORECASE)
    # Удаляем остальные теги
    text = re.sub(r'<[^>]+>', ' ', text)
    # Сжимаем пробелы
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def process_file(file_path: Path):
    ext = file_path.suffix.lower()
    content = ""
    
    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
        if not raw_text:
            return None
        title = file_path.stem.replace("_", " ").replace("-", " ").title()
        content = f"# {title} (PDF Даташит/Документация)\n\n"
        content += f"> Исходный файл: `{file_path.name}`\n\n"
        content += raw_text

    elif ext in [".html", ".htm"]:
        raw_html = file_path.read_text(encoding='utf-8', errors='ignore')
        title = file_path.stem.replace("_", " ").title()
        cleaned = clean_html(raw_html)
        content = f"# {title}\n\n> Источник: `{file_path.name}`\n\n{cleaned}"

    elif ext in [".txt", ".md"]:
        raw = file_path.read_text(encoding='utf-8', errors='ignore')
        if ext == ".md" and raw.startswith("#"):
            content = raw
        else:
            title = file_path.stem.replace("_", " ").title()
            content = f"# {title}\n\n{raw}"

    return content

def main():
    print("🚀 Запуск пайплайна импорта документации из raw_docs/...")
    
    files = list(PDF_DIR.glob("*.*")) + list(POSTS_DIR.glob("*.*")) + list(NOTES_DIR.glob("*.*"))
    # Исключаем README и служебные файлы
    files = [f for f in files if f.is_file() and f.name.lower() != "readme.md"]

    if not files:
        print("ℹ️ В папках raw_docs/ (pdf, posts, notes) пока нет новых файлов для конвертации.")
        print("   Положите туда PDF даташиты, сохраненные посты или заметки и запустите снова.")
        return

    converted = 0
    for f in files:
        out_name = f"doc_{f.stem}.md"
        out_path = DOCS_DIR / out_name
        print(f"📄 Обработка: {f.name} -> {out_name}...")
        
        md_text = process_file(f)
        if md_text:
            out_path.write_text(md_text, encoding='utf-8')
            converted += 1
            print(f"  ✅ Сохранено в {out_path.name} ({len(md_text)} символов)")

    print(f"\n🎉 Обработано и конвертировано: {converted} файлов.")

    # Автоматически обновляем базу знаний SQLite FTS5
    if converted > 0:
        print("🔄 Обновление локальной базы знаний FTS5...")
        try:
            import subprocess
            subprocess.run([sys.executable, str(SCRIPTS_DIR / "build_local_kb_sqlite.py")], check=True)
            print("✅ Локальная база omni_knowledge.db успешно актуализирована!")
        except Exception as e:
            print(f"Ошибка обновления базы: {e}")

if __name__ == "__main__":
    main()
