# 04. Подключение Инструментов на ПК, Claude Code, MCP-Сервер и Конфигурации IDE

Данный документ описывает интеграцию кластера **Triad-Omni v4.7** с вашей средой разработки на ПК: консольным агентом **Claude Code**, редакторами **Cursor / VS Code (Continue)** и протоколом **Model Context Protocol (MCP)** с поддержкой графа знаний **Graphify**.

---

## 1. Универсальный MCP-Сервер на ПК (`omni_mcp_server.py`)

Сервер MCP реализует стандартный протокол JSON-RPC через `stdio` и объединяет:
1. **Инструменты смарт-кластера**: вызов моделей смартфонов (`ask_triad_cluster`), сохранение навыков в SQLite FTS5 (`save_skill_to_cluster`), каскадную эскалацию ошибок (`escalate_to_teacher`).
2. **Инструменты графа знаний Graphify**: быстрый обход архитектуры репозитория (`graphify_query`), трассировку связей между компонентами (`graphify_path`), детальный разбор узлов (`graphify_explain`) и обзор архитектурных центров (`graphify_god_nodes`).

Полный файл сервера находится в корне проекта: [`omni_mcp_server.py`](file:///d:/для%20one%20plus%20nord%20n10/omni_mcp_server.py).

### Доступные инструменты (Tools):
* `ask_triad_cluster` — запрос к локальному ИИ-кластеру смартфонов (Пайка ГОСТ/IPC, Ghidra ReVa, ESP32, Vision).
* `save_skill_to_cluster` — сохранение правила или распиновки в базу знаний шлюза Note 4 и очередь дообучения.
* `escalate_to_teacher` — эскалация ошибки компиляции: в DeepSeek Flash (открытые задачи) или локальный MoE-учитель на ПК (приватный реверс Android).
* `graphify_query` — направленный обход графа (BFS/DFS) с жестким бюджетом токенов (возвращает сжатый релевантный контекст без чтения сотен файлов).
* `graphify_path` — кратчайший путь и граф вызовов между модулем А и модулем Б.
* `graphify_explain` — детальный разбор структуры любого файла/класса со всеми входящими и исходящими связями.
* `graphify_god_nodes` — список главных управляющих узлов (God Nodes) системы.

---

## 2. Подключение в Claude Code и Claude Desktop

### Вариант А: Конфигурация Claude Desktop (`claude_desktop_config.json`)
Добавьте сервер в ваш файл конфигурации (`%APPDATA%\Claude\claude_desktop_config.json` на Windows или `~/.config/Claude/claude_desktop_config.json` на Linux):

```json
{
  "mcpServers": {
    "triad-omni": {
      "command": "python",
      "args": ["d:/для one plus nord n10/omni_mcp_server.py"],
      "env": {
        "HUB_URL": "http://192.168.1.203:8000",
        "OMNI_TOKEN": "ВАШ_OMNI_TOKEN"
      }
    }
  }
}
```

### Вариант Б: Claude Code CLI в терминале
Для запуска Claude Code с перенаправлением на шлюз Redmi Note 4 добавьте алиас в `~/.bashrc`:

```bash
# Добавить в ~/.bashrc
source ~/omni_auto_trainer/omni_env.sh
alias claude-omni='ANTHROPIC_BASE_URL="http://192.168.1.203:8000" ANTHROPIC_API_KEY="$OMNI_TOKEN" ANTHROPIC_MODEL="omni-auto" ANTHROPIC_SMALL_FAST_MODEL="omni-fast" claude'
```

---

## 3. Настройка расширения Continue (VS Code / VSCodium / Cursor)

В файле конфигурации Continue (`~/.continue/config.json`):

```json
{
  "models": [
    {
      "title": "Triad Omni (Auto Router)",
      "provider": "openai",
      "model": "omni-auto",
      "apiBase": "http://192.168.1.203:8000/v1",
      "apiKey": "ВАШ_OMNI_TOKEN"
    },
    {
      "title": "Triad Fast Reflex (Nord N10)",
      "provider": "openai",
      "model": "omni-fast",
      "apiBase": "http://192.168.1.203:8000/v1",
      "apiKey": "ВАШ_OMNI_TOKEN"
    },
    {
      "title": "Triad Local MoE Teacher (PC 30B)",
      "provider": "openai",
      "model": "omni-teacher",
      "apiBase": "http://192.168.1.203:8000/v1",
      "apiKey": "ВАШ_OMNI_TOKEN"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Nord N10 Fast Tab Autocomplete",
    "provider": "openai",
    "model": "omni-fast",
    "apiBase": "http://192.168.1.203:8000/v1",
    "apiKey": "ВАШ_OMNI_TOKEN"
  }
}
```

---

## 4. Скрипт быстрой раскатки файлов с ПК на смартфоны

Создайте `~/omni_auto_trainer/deploy_all_nodes.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
source "$HOME/omni_auto_trainer/omni_env.sh"

echo "Раскатка конфигураций и скриптов по узлам кластера..."

# 1. Смартфоны Mi 10T и Nord N10
for ip in 201 202; do
  echo "Копирование omni_env.sh и node_telemetry.sh на 192.168.1.$ip..."
  scp -P 8022 ~/omni_auto_trainer/omni_env.sh node_telemetry.sh 192.168.1.$ip:~/
done

# 2. Mi 10T (Мозг)
echo "Копирование скриптов на Mi 10T..."
scp -P 8022 start_brain.sh thermal_guard.sh preflight.sh 192.168.1.201:~/
ssh -p 8022 192.168.1.201 "chmod +x ~/start_brain.sh ~/thermal_guard.sh ~/preflight.sh ~/node_telemetry.sh"

# 3. Nord N10 (Рефлекс)
echo "Копирование скриптов на Nord N10..."
scp -P 8022 start_reflex.sh 192.168.1.202:~/.termux/boot/
ssh -p 8022 192.168.1.202 "chmod +x ~/.termux/boot/start_reflex.sh ~/node_telemetry.sh"

# 4. Note 4 (Шлюз)
echo "Копирование шлюза на Note 4..."
scp -P 8022 ~/omni_auto_trainer/omni_env.sh omni_gateway.py 192.168.1.203:~/omni_hub/
ssh -p 8022 192.168.1.203 "chmod +x ~/omni_hub/omni_gateway.py"

echo "✅ Раскатка завершена успешно."
```
```bash
chmod +x ~/omni_auto_trainer/deploy_all_nodes.sh
```
