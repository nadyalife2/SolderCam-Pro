#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Unified MCP Server v5.1 (Fully Compliant with MCP Protocol 2024-11-05)
Supports:
  1. Full JSON-RPC 2.0 Handshake (initialize, ping, notifications/initialized).
  2. Zero-latency Cluster Gateway Access (Mi 10T 5G, Nord N10 5G, Redmi Note 4).
  3. Seamless DeepSeek Harness, Claude Code CLI, Continue, and Cursor Integration.
  4. Graphify Knowledge Graph Tools (15,000+ nodes, BFS/DFS pathfinding, god nodes).
  5. Multi-Hub Fallback (LAN -> localhost loopback).
"""
import sys
import os
import json
import subprocess
import urllib.request
import urllib.error

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))

def load_cluster_env():
    env_file = os.path.join(WORKSPACE_ROOT, "config", "cluster.env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

load_cluster_env()

HUB = os.environ.get("HUB_URL", "http://127.0.0.1:8000")
TOKEN = os.environ.get("OMNI_TOKEN", "sk-triad")
FALLBACK_HUBS = [
    HUB,
    "http://127.0.0.1:8000",
    "http://192.168.31.48:8000",
    "http://192.168.31.161:8000",
    "http://192.168.31.161:8080"
]

def call_hub(path, data):
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["X-Omni-Token"] = TOKEN
        headers["Authorization"] = f"Bearer {TOKEN}"

    payload = json.dumps(data).encode("utf-8")
    last_err = None

    # Try primary and fallback hubs
    tried = []
    for base in FALLBACK_HUBS:
        if base in tried:
            continue
        tried.append(base)
        target_url = f"{base.rstrip('/')}{path}"
        try:
            req = urllib.request.Request(target_url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as he:
            # If server returned HTTP error body, try to parse JSON
            try:
                body = he.read().decode("utf-8")
                return json.loads(body)
            except Exception:
                last_err = he
        except Exception as e:
            last_err = e
            continue

    return {"error": f"Все хабы кластера недоступны ({tried}): {last_err}"}

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

        # 1. MCP Protocol Handshake: initialize
        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "triad-omni-mcp",
                        "version": "5.1"
                    }
                }
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        # 2. MCP Protocol Handshake: ping
        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        # 3. MCP Protocol Handshake: notifications/initialized (notification, no id)
        elif method == "notifications/initialized":
            pass

        # 4. MCP Tools List
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        # 5. MCP Tool Call
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
                        "messages": [{"role": "user", "content": prompt}],
                        "prompt": prompt
                    })
                    if isinstance(out, dict):
                        choices = out.get("choices")
                        if choices and isinstance(choices, list) and len(choices) > 0:
                            first_choice = choices[0]
                            if isinstance(first_choice, dict):
                                msg = first_choice.get("message")
                                if isinstance(msg, dict) and "content" in msg:
                                    txt = msg.get("content", "")
                                elif "text" in first_choice:
                                    txt = first_choice.get("text", "")
                                else:
                                    txt = str(first_choice)
                            else:
                                txt = str(first_choice)
                        elif "content" in out:
                            txt = out.get("content", "")
                        elif "error" in out:
                            txt = f"⚠️ Ошибка от кластера: {out.get('error')}"
                        else:
                            txt = json.dumps(out, ensure_ascii=False)
                    else:
                        txt = str(out)

                elif tname == "save_skill_to_cluster":
                    out = call_hub("/v1/sync_skill", args)
                    txt = f"Сохранено: {out.get('topic') or out.get('message') or out}"

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

        # Any other method with an ID: return method not found or empty result
        elif msg_id is not None:
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
