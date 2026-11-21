#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Unified MCP Server v4.8
Объединяет:
  1. Доступ к кластеру смартфонов (Redmi Note 4, Mi 10T, Nord N10).
  2. Каскад эскалации ошибок (DeepSeek Flash 4.1 + локальный MoE-учитель).
  3. Персистентный граф знаний Graphify (15 000+ узлов, поиск связей, BFS/DFS, god-ноды).
"""
import sys
import os
import json
import subprocess
import urllib.request

HUB = os.environ.get("HUB_URL", "http://192.168.1.203:8000")
TOKEN = os.environ.get("OMNI_TOKEN", "")
WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))

def call_hub(path, data):
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["X-Omni-Token"] = TOKEN
    req = urllib.request.Request(
        f"{HUB}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers=headers
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))

def run_graphify(*args):
    try:
        cmd = ["graphify", *args]
        r = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = r.stdout.strip()
        if not out and r.stderr:
            out = r.stderr.strip()
        return out or "Нет данных от graphify"
    except Exception as e:
        return f"Ошибка вызова graphify: {e}"

TOOLS = [
    {
        "name": "ask_triad_cluster",
        "description": "Запрос к локальному ИИ-кластеру смартфонов (Пайка ГОСТ/IPC, Ghidra ReVa, ESP32, Vision)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Текст запроса"},
                "model": {"type": "string", "default": "omni-auto", "description": "Модель (omni-auto, omni-fast, omni-teacher, omni-vision)"}
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "save_skill_to_cluster",
        "description": "Мгновенно сохранить правило, ГОСТ или распиновку в базу знаний кластера и очередь LoRA",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Название навыка или файла"},
                "content": {"type": "string", "description": "Содержимое правила"},
                "source_folder": {"type": "string", "default": "ide_agent"}
            },
            "required": ["topic", "content"]
        }
    },
    {
        "name": "escalate_to_teacher",
        "description": "Эскалация ошибки верификации/компиляции: DeepSeek Flash (общие домены) или локальный MoE-учитель на ПК (reva_android)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Домен (solder, esp32, reva_android)"},
                "prompt": {"type": "string", "description": "Исходный запрос"},
                "reply": {"type": "string", "description": "Сгенерированный ошибочный ответ"},
                "error": {"type": "string", "description": "Текст ошибки компилятора или лога"}
            },
            "required": ["domain", "prompt", "error"]
        }
    },
    {
        "name": "graphify_query",
        "description": "Запрос к графу знаний кодовой базы (15 000+ узлов). Возвращает структурированный контекст связей и определений с жестким лимитом токенов.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Архитектурный вопрос (например: 'Как устроен шлюз?' или 'Где логируется батарея?')"},
                "budget": {"type": "integer", "default": 1500, "description": "Лимит токенов на ответ"},
                "dfs": {"type": "boolean", "default": False, "description": "Использовать глубокий DFS вместо BFS для трассировки цепочки"}
            },
            "required": ["question"]
        }
    },
    {
        "name": "graphify_path",
        "description": "Поиск кратчайшего пути и взаимосвязей между двумя компонентами, модулями или файлами в графе знаний",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Начальный узел или файл (например: 'omni_gateway.py')"},
                "target": {"type": "string", "description": "Конечный узел или файл (например: 'start_brain.sh')"}
            },
            "required": ["source", "target"]
        }
    },
    {
        "name": "graphify_explain",
        "description": "Детальное объяснение конкретного узла, файла или концепта с входящими и исходящими связями",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node": {"type": "string", "description": "Имя узла, функции или файла"}
            },
            "required": ["node"]
        }
    },
    {
        "name": "graphify_god_nodes",
        "description": "Получить список ключевых архитектурных ядер системы (центральных управляющих узлов)",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
        except Exception:
            continue

        method = req.get("method")
        msg_id = req.get("id")

        if method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            params = req.get("params", {})
            tname = params.get("name")
            args = params.get("arguments", {})

            txt = ""
            try:
                if tname == "ask_triad_cluster":
                    prompt = args.get("prompt", "")
                    m = args.get("model", "omni-auto")
                    out = call_hub("/v1/chat/completions", {
                        "model": m,
                        "messages": [{"role": "user", "content": prompt}]
                    })
                    ans = out.get("choices", [{}])[0].get("message", {}).get("content", "")
                    txt = ans

                elif tname == "save_skill_to_cluster":
                    out = call_hub("/v1/sync_skill", args)
                    txt = f"Сохранено: {out.get('topic')}"

                elif tname == "escalate_to_teacher":
                    out = call_hub("/v1/escalate", args)
                    txt = json.dumps(out, ensure_ascii=False)

                elif tname == "graphify_query":
                    q = args.get("question", "")
                    budget = args.get("budget", 1500)
                    cmd = ["query", q, "--budget", str(budget)]
                    if args.get("dfs", False):
                        cmd.append("--dfs")
                    txt = run_graphify(*cmd)

                elif tname == "graphify_path":
                    src = args.get("source", "")
                    dst = args.get("target", "")
                    txt = run_graphify("path", src, dst)

                elif tname == "graphify_explain":
                    node = args.get("node", "")
                    txt = run_graphify("explain", node)

                elif tname == "graphify_god_nodes":
                    analysis_file = os.path.join(WORKSPACE_ROOT, "graphify-out", ".graphify_analysis.json")
                    if os.path.exists(analysis_file):
                        try:
                            d = json.load(open(analysis_file, encoding="utf-8"))
                            gods = d.get("gods", [])
                            txt = "🔥 Ключевые архитектурные узлы (God Nodes):\n" + "\n".join(f"- {g}" for g in gods[:20])
                        except Exception as e:
                            txt = f"Ошибка чтения analysis: {e}"
                    else:
                        txt = "Файл анализа graphify-out/.graphify_analysis.json не найден."

                else:
                    txt = f"Неизвестный инструмент: {tname}"

            except Exception as e:
                txt = f"Ошибка выполнения {tname}: {e}"

            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": txt}]}
            }
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
