#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Harness Exporter
Экспортирует все навыки (skills), правила (rules), авторский профиль, MCP-сервер
и базу знаний из Antigravity в любой внешний ИИ-харнесс на ПК (DeepSeek Harness, Claude Code, Cursor и др.).

Использование:
  python export_to_harness.py                           # Создает папку exported_harness_bundle
  python export_to_harness.py --zip                     # Создает единый архив triad_harness_bundle.zip
  python export_to_harness.py --target-dir "C:/path"   # Копирует напрямую в целевую папку харнесса
"""
import os
import sys
import shutil
import zipfile
import argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_SKILLS_DIR = os.path.join(ROOT, ".agents", "skills")
GLOBAL_SKILLS_DIR = os.path.expanduser(r"~\.gemini\config\skills")

def parse_args():
    parser = argparse.ArgumentParser(description="Экспорт всех навыков и правил в сторонний агентный харнесс.")
    parser.add_argument("--target-dir", default=os.path.join(ROOT, "exported_harness_bundle"), help="Куда сохранить бандл")
    parser.add_argument("--zip", action="store_true", help="Упаковать результат в zip-архив")
    parser.add_argument("--zip-name", default=os.path.join(ROOT, "triad_harness_bundle.zip"), help="Имя zip-архива")
    return parser.parse_args()

def copy_tree_filtered(src, dst):
    """Копирует дерево файлов, пропуская временные файлы, кэши и системные логи."""
    def ignore_patterns(folder, files):
        ignored = set()
        for f in files:
            if f in ("__pycache__", ".git", ".pytest_cache", ".venv", "node_modules"):
                ignored.add(f)
            elif f.endswith((".pyc", ".pyo", ".pyd")):
                ignored.add(f)
        return ignored

    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True, ignore=ignore_patterns)
        else:
            shutil.copy2(s, d)

def main():
    args = parse_args()
    target = os.path.abspath(args.target_dir)
    print(f"📦 Сборка бандла навыков и конфигурации в: {target}")

    skills_dst = os.path.join(target, "skills")
    rules_dst = os.path.join(target, "rules")
    knowledge_dst = os.path.join(target, "knowledge")
    mcp_dst = os.path.join(target, "mcp")

    os.makedirs(skills_dst, exist_ok=True)
    os.makedirs(rules_dst, exist_ok=True)
    os.makedirs(knowledge_dst, exist_ok=True)
    os.makedirs(mcp_dst, exist_ok=True)

    # 1. Экспорт локальных навыков репозитория
    if os.path.exists(LOCAL_SKILLS_DIR):
        print(f"  -> Копирование локальных навыков из {LOCAL_SKILLS_DIR}...")
        for skill in os.listdir(LOCAL_SKILLS_DIR):
            skill_src = os.path.join(LOCAL_SKILLS_DIR, skill)
            if os.path.isdir(skill_src):
                skill_target = os.path.join(skills_dst, skill)
                copy_tree_filtered(skill_src, skill_target)
                print(f"     [+] Скил: {skill}")

    # 2. Экспорт глобального скила impeccable (дизайн и верстка UI)
    impeccable_src = os.path.join(GLOBAL_SKILLS_DIR, "impeccable")
    if os.path.exists(impeccable_src):
        copy_tree_filtered(impeccable_src, os.path.join(skills_dst, "impeccable"))
        print("     [+] Скил: impeccable (глобальный дизайн-скил)")

    # 3. Экспорт правил и авторского голоса
    print("  -> Экспорт правил, профилей и гайдов...")
    for rule_file in ("USER_VOICE_STYLE_GUIDE.md", "GEMINI.md"):
        src_path = os.path.join(ROOT, rule_file)
        if os.path.exists(src_path):
            shutil.copy2(src_path, os.path.join(rules_dst, rule_file))

    agents_rule = os.path.join(ROOT, ".agents", "rules", "AGENTS.md")
    if os.path.exists(agents_rule):
        shutil.copy2(agents_rule, os.path.join(rules_dst, "AGENTS.md"))
        # Для Claude Code и Cursor создаем их стандартные алиасы
        shutil.copy2(agents_rule, os.path.join(rules_dst, "CLAUDE.md"))
        shutil.copy2(agents_rule, os.path.join(rules_dst, ".cursorrules"))

    # 4. Экспорт MCP-сервера
    mcp_src = os.path.join(ROOT, "omni_mcp_server.py")
    if os.path.exists(mcp_src):
        shutil.copy2(mcp_src, os.path.join(mcp_dst, "omni_mcp_server.py"))
        print("  -> Экспорт MCP-сервера (omni_mcp_server.py)")

    # 5. Экспорт архитектурных документов cluster_docs
    cluster_docs_src = os.path.join(ROOT, "cluster_docs")
    if os.path.exists(cluster_docs_src):
        copy_tree_filtered(cluster_docs_src, os.path.join(knowledge_dst, "cluster_docs"))
        print("  -> Экспорт проектной документации cluster_docs (01–08)")

    # 6. Экспорт графа знаний и вики
    wiki_src = os.path.join(ROOT, "graphify-out", "wiki")
    if os.path.exists(wiki_src):
        copy_tree_filtered(wiki_src, os.path.join(knowledge_dst, "wiki"))
        print("  -> Экспорт Markdown-Вики графа знаний (graphify wiki)")

    # 7. Генерация инструкций по подключению README.md
    readme_content = f"""# Triad-Omni Agent Bundle (Skills, Rules & MCP)

Данный архив содержит полный переносимый комплект навыков, системных инструкций и MCP-инструментов, экспортированный из среды Antigravity.

## Состав комплекта:
1. **`skills/`** — 12 специализированных навыков (`SKILL.md`):
   - `gadget-camera-tuning` (сенсоры, Camera2 API, PMIC/NTC)
   - `mobile-android-design` (Material Design 3, UI/UX)
   - `awesome-rea` (база знаний по реверсу)
   - `reverse-engineer-anything` (декомпиляция и анализ прошивок)
   - `budget-tablet-unmasking-tuning` (аппаратный анмаскинг и AOT)
   - `melvin-edge-ai` (on-device LLM, PRoot Alpine, Bionic)
   - `graphify` (GraphRAG, анализ архитектуры кодовой базы)
   - `impeccable` (профессиональный фронтенд и дизайн)
   - инструментарий REA (анализ, тулы, тесты, ченджлог)

2. **`rules/`** — системные правила и авторский голос:
   - `AGENTS.md` / `CLAUDE.md` / `.cursorrules` — правила для агента.
   - `USER_VOICE_STYLE_GUIDE.md` — профиль голоса автора (женский род прошедшего времени, живой темп, zero fluff).

3. **`mcp/`** — универсальный сервер `omni_mcp_server.py` (7 инструментов для вызова телефонов, Graphify и эскалации).

4. **`knowledge/`** — база знаний:
   - `cluster_docs/` — спецификации 01–08 по сборке и питанию кластера.
   - `wiki/` — офлайн-вики графа знаний на 954 статьи.

---

## Как подключить к стороннему харнессу на ПК:

### Вариант 1: DeepSeek Harness
Скопируйте папку `skills/` в директорию навыков вашего харнесса:
```bash
cp -r skills/* ~/deepseek-harness/skills/
cp rules/AGENTS.md ~/deepseek-harness/system_prompt.md
```

### Вариант 2: Claude Code CLI
```bash
cp rules/CLAUDE.md ~/CLAUDE.md
cp -r skills/* ~/.claude/skills/
```

### Вариант 3: Cursor / VS Code
Поместите `rules/.cursorrules` в корень вашего рабочего репозитория.

### Вариант 4: Подключение MCP
В конфигурацию MCP любого агента (`claude_desktop_config.json`):
```json
{{
  "mcpServers": {{
    "triad-omni": {{
      "command": "python",
      "args": ["{os.path.join(mcp_dst, 'omni_mcp_server.py').replace(os.sep, '/')}"],
      "env": {{
        "HUB_URL": "http://192.168.1.203:8000",
        "OMNI_TOKEN": "ВАШ_OMNI_TOKEN"
      }}
    }}
  }}
}}
```
"""
    with open(os.path.join(target, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    # 8. Создание zip-архива при необходимости
    if args.zip:
        zip_path = os.path.abspath(args.zip_name)
        print(f"  -> Упаковка архива {zip_path}...")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(target):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, target)
                    zf.write(full_p, rel_p)
        print(f"🎉 Готово! Архив создан: {zip_path}")
    else:
        print(f"🎉 Готово! Бандл собран в: {target}")

if __name__ == "__main__":
    main()
