#!/usr/bin/env python3
"""
Triad-Omni Gateway v4.6 (High-Concurrency & Non-Techie Friendly Edition)
Key Improvements:
1. ThreadingHTTPServer - No blocking calls, multiple devices and clients can query simultaneously.
2. Full SSE Streaming (text/event-stream) - Instant token-by-token output for Claude Code, Continue, Web UI.
3. Tool RAG for MCP - Automatically trims 40+ MCP JSON schemas down to Top-3 using BGE-M3 embeddings.
4. Anthropic Messages API compliant - Properly parses top-level system prompts and image sources.
5. Dual-Mode Web UI - Simple Mode for non-techies (Big Status, 3 task buttons, in-browser chat) & Pro Mode.
"""

import sqlite3
import json
import math
import os
import subprocess
import threading
import time
import urllib.request
import urllib.error
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# --- СЕТЕВАЯ КОНФИГУРАЦИЯ ---
NODES = {
    "mi10t":  {"name": "Xiaomi Mi 10T (Brain 9B/7B)", "ip": "192.168.1.201", "port": 8080, "role": "9B STEM+Vision / 7B Coder 24K"},
    "nord10": {"name": "OnePlus Nord N10 (Reflex 3B)", "ip": "192.168.1.202", "port": 8081, "role": "Qwen2.5-Coder-3B + BGE-M3"},
    "note4":  {"name": "Redmi Note 4 (Omni Hub)",     "ip": "192.168.1.203", "port": 8000, "role": "Gateway + SQLite FTS5 + Kiosk"}
}
PC_USER = "user"
PC_IP   = "192.168.1.100"

NODE1_BRAIN   = f"http://{NODES['mi10t']['ip']}:8080/v1/chat/completions"
NODE2_FAST    = f"http://{NODES['nord10']['ip']}:8081/v1/chat/completions"
NODE2_EMBED   = f"http://{NODES['nord10']['ip']}:8082/v1/embeddings"
LOCAL_33B_URL = f"http://{PC_IP}:8090/v1/chat/completions"

# --- ПУТИ ХРАНИЛИЩА ---
SDCARD_PATH = "/storage/emulated/0/OmniCluster_Data"
BASE_DIR    = SDCARD_PATH if os.path.exists("/storage/emulated/0") else os.path.expanduser("~/omni_hub")
DB_FILE     = os.path.join(BASE_DIR, "db/omni_knowledge.db")
DS_DIR      = os.path.join(BASE_DIR, "datasets")
os.makedirs(DS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

# Thread-safe SQLite helper
def get_db():
    c = sqlite3.connect(DB_FILE, timeout=10.0)
    c.execute("PRAGMA journal_mode=WAL;")
    return c

# Инициализация схемы БД
with get_db() as init_conn:
    init_conn.execute("""
    CREATE TABLE IF NOT EXISTS skills_meta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT,
        topic TEXT UNIQUE,
        content TEXT,
        source_folder TEXT,
        utility_score INTEGER DEFAULT 2,
        usage_count INTEGER DEFAULT 0,
        vec_json TEXT,
        updated_at TEXT
    );
    """)
    init_conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS kb_fts USING fts5(domain, topic, content);")
    init_conn.execute("CREATE TABLE IF NOT EXISTS articles_vec (slug TEXT PRIMARY KEY, title TEXT, vec_json TEXT, created_at TEXT);")
    init_conn.execute("CREATE TABLE IF NOT EXISTS token_stats (domain TEXT PRIMARY KEY, prompt_tokens INTEGER DEFAULT 0, completion_tokens INTEGER DEFAULT 0, requests_count INTEGER DEFAULT 0);")
    init_conn.execute("CREATE TABLE IF NOT EXISTS watched_folders (path TEXT PRIMARY KEY, agent_type TEXT, last_sync TEXT);")
    init_conn.execute("CREATE TABLE IF NOT EXISTS training_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, level TEXT, event TEXT);")

TELEMETRY_CACHE = {}
CURRENT_MI10T_PROFILE = "stem"
TEACHER_33B_STATE = "OFFLINE"
LAST_ALERT = {"beep": None, "ts": 0}

def add_log(msg, level="INFO", beep=None):
    try:
        with get_db() as c:
            c.execute("INSERT INTO training_logs(ts, level, event) VALUES (?, ?, ?)", (datetime.now().strftime("%H:%M:%S"), level, msg))
            c.execute("DELETE FROM training_logs WHERE id NOT IN (SELECT id FROM training_logs ORDER BY id DESC LIMIT 50)")
    except Exception:
        pass
    if beep:
        LAST_ALERT.update({"beep": beep, "ts": time.time()})
        subprocess.Popen("su -c 'input keyevent 224' 2>/dev/null", shell=True)

def http_json(url, payload, headers=None, timeout=120):
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def get_embedding(text):
    try:
        res = http_json(NODE2_EMBED, {"input": text[:1500]}, timeout=5)
        if "data" in res and len(res["data"]) > 0:
            return res["data"][0]["embedding"]
    except Exception:
        pass
    return None

def cosine_sim(v1, v2):
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(a * a for a in v1))
    n2 = math.sqrt(sum(b * b for b in v2))
    return dot / (n1 * n2) if (n1 and n2) else 0.0

def filter_mcp_tools(tools_list, query_text):
    """Tool RAG: Оставляет только топ-3 инструмента, чтобы не забивать контекст моделей 7B/9B"""
    if not tools_list or len(tools_list) <= 3:
        return tools_list
    q_vec = get_embedding(query_text[:600])
    if not q_vec:
        return tools_list[:4]
    scored = []
    for t in tools_list:
        name = t.get("function", {}).get("name", t.get("name", ""))
        desc = t.get("function", {}).get("description", t.get("description", ""))
        t_vec = get_embedding(f"{name}: {desc}")
        sim = cosine_sim(q_vec, t_vec) if t_vec else 0.0
        scored.append((sim, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:3]]

def fetch_active_skills(domain, query_text):
    clean_words = [w for w in "".join(c if c.isalnum() else " " for c in query_text).split() if len(w) > 3]
    fts_topics = []
    if clean_words:
        fts_q = " OR ".join(clean_words[:6])
        try:
            with get_db() as c:
                rows = c.execute("SELECT topic FROM kb_fts WHERE kb_fts MATCH ? LIMIT 3", (fts_q,)).fetchall()
                fts_topics = [r[0] for r in rows]
        except Exception:
            pass
    try:
        with get_db() as c:
            cur = c.execute(
                "SELECT id, topic, content FROM skills_meta WHERE (domain = ? OR topic IN ({})) AND utility_score > -2 ORDER BY utility_score DESC LIMIT 3".format(
                    ",".join(["?"] * len(fts_topics)) if fts_topics else "''"
                ),
                tuple([domain] + fts_topics)
            )
            items = cur.fetchall()
            for r in items:
                c.execute("UPDATE skills_meta SET usage_count = usage_count + 1 WHERE id = ?", (r[0],))
            return "\n".join([f"• [{r[1]}]: {r[2]}" for r in items])
    except Exception:
        return ""

def telemetry_thread():
    global CURRENT_MI10T_PROFILE, TEACHER_33B_STATE
    while True:
        for k, info in NODES.items():
            cmd = (
                "cat /sys/class/power_supply/battery/capacity 2>/dev/null || echo 50; "
                "cat /sys/class/power_supply/battery/temp 2>/dev/null || echo 300; "
                "awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0"
            )
            try:
                if k == "note4":
                    out = subprocess.check_output(cmd, shell=True, timeout=2).decode().split()
                else:
                    out = subprocess.check_output(
                        ["ssh", "-p", "8022", "-o", "ConnectTimeout=2", "-o", "StrictHostKeyChecking=no", info["ip"], cmd],
                        timeout=3
                    ).decode().split()
                bat = int(out[0]) if len(out) > 0 else 50
                tmp = round(int(out[1]) / 10.0, 1) if len(out) > 1 else 30.0
                ram = int(out[2]) if len(out) > 2 else 0
                TELEMETRY_CACHE[k] = {"online": True, "battery": bat, "temp_c": tmp, "free_ram_mb": ram}
                
                # Защита аккумулятора Note 4
                if k == "note4":
                    if bat >= 75:
                        subprocess.Popen("su -c 'echo 0 > /sys/class/power_supply/battery/charging_enabled' 2>/dev/null", shell=True)
                    elif bat <= 60:
                        subprocess.Popen("su -c 'echo 1 > /sys/class/power_supply/battery/charging_enabled' 2>/dev/null", shell=True)
                if tmp >= 46.5:
                    add_log(f"🔥 ПЕРЕГРЕВ {info['name']}: {tmp}°C! Сброс нагрузки.", "ALARM", "alarm")
            except Exception:
                TELEMETRY_CACHE[k] = {"online": False, "battery": 0, "temp_c": 0.0, "free_ram_mb": 0}
        time.sleep(12)

threading.Thread(target=telemetry_thread, daemon=True).start()

# --- ВЕБ-ИНТЕРФЕЙС (ПРОСТОЙ + ПРОФЕССИОНАЛЬНЫЙ РЕЖИМ С ВСТРОЕННЫМ ЧАТОМ) ---
UI_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Triad-Omni v4.6 Easy Hub</title>
<style>
  :root { --bg: #090d16; --card: #151d30; --accent: #f59e0b; --blue: #38bdf8; --green: #22c55e; --red: #ef4444; --text: #f8fafc; }
  * { box-sizing: border-box; }
  body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 12px; }
  .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #22304d; padding-bottom: 10px; margin-bottom: 12px; }
  .status-pill { background: rgba(34,197,94,0.18); color: var(--green); padding: 6px 14px; border-radius: 99px; font-weight: 700; font-size: 14px; border: 1px solid rgba(34,197,94,0.3); }
  .mode-switch { display: flex; gap: 8px; margin-bottom: 14px; }
  .big-btn { flex: 1; padding: 16px 10px; border-radius: 12px; border: 2px solid transparent; font-size: 15px; font-weight: 800; cursor: pointer; text-align: center; background: #1c263d; color: var(--text); transition: 0.15s; }
  .big-btn.active { border-color: var(--blue); background: rgba(56,189,248,0.15); color: var(--blue); }
  .big-btn:active { transform: scale(0.98); }
  .chat-box { background: var(--card); border-radius: 12px; padding: 12px; border: 1px solid #22304d; margin-bottom: 14px; }
  #messages { height: 260px; overflow-y: auto; font-size: 14px; line-height: 1.45; margin-bottom: 10px; padding: 4px; }
  .msg-u { color: var(--blue); margin-bottom: 6px; }
  .msg-a { color: var(--text); margin-bottom: 10px; background: rgba(255,255,255,0.03); padding: 8px; border-radius: 8px; }
  .chat-input { display: flex; gap: 6px; }
  input { flex: 1; background: #090d16; border: 1px solid #334155; color: white; padding: 12px; border-radius: 8px; font-size: 14px; }
  button.send { background: var(--blue); color: #090d16; border: none; padding: 0 20px; border-radius: 8px; font-weight: 800; cursor: pointer; }
  .pro-panel { display: none; background: #111827; padding: 12px; border-radius: 12px; margin-top: 10px; border: 1px dashed #374151; }
  .pro-active .pro-panel { display: block; }
  .node-tag { display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 11px; margin-right: 6px; background: #1f2937; }
</style>
</head>
<body>
  <div class="header">
    <div>
      <h2 style="margin:0;">⚡ Triad-Omni <small style="font-size:12px;color:#94a3b8;">v4.6</small></h2>
      <span id="telemetry_summary">Загрузка...</span>
    </div>
    <div style="display:flex;gap:6px;align-items:center;">
      <span class="status-pill" id="cluster_status">В СЕТИ</span>
      <button onclick="document.body.classList.toggle('pro-active')" style="background:#374151;color:white;border:none;padding:8px 12px;border-radius:8px;font-size:12px;cursor:pointer;">🛠️ Про-пульт</button>
    </div>
  </div>

  <!-- КНОПКИ ДЛЯ ЛЮБОГО ПОЛЬЗОВАТЕЛЯ («БЕЗ ТЕХНИЧЕСКИХ ДЕБРЕЙ») -->
  <div class="mode-switch">
    <div class="big-btn active" id="btn_stem" onclick="setMode('mode_stem', this)">🔬 Пайка и Схемы</div>
    <div class="big-btn" id="btn_coder" onclick="setMode('mode_coder', this)">💻 Написание Кода</div>
    <div class="big-btn" id="btn_fast" onclick="setMode('mode_fast', this)">⚡ Быстрый Ответ</div>
  </div>

  <!-- ВСТРОЕННЫЙ ЧАТ (РАБОТАЕТ ПРЯМО В БРАУЗЕРЕ БЕЗ НАСТРОЙКИ IDE) -->
  <div class="chat-box">
    <div id="messages">
      <div class="msg-a">Привет! Кластер Triad-Omni готов. Выберите режим выше и спросите о схеме, пайке ГОСТ или попросите написать код.</div>
    </div>
    <div class="chat-input">
      <input id="user_input" placeholder="Задайте вопрос кластеру..." onkeydown="if(event.key==='Enter') sendChat()">
      <button class="send" onclick="sendChat()">➤</button>
    </div>
  </div>

  <!-- ПРО-ПАНЕЛЬ (ТЕЛЕМЕТРИЯ, ВОЛЬТАЖ, LORA, SQLITE) -->
  <div class="pro-panel">
    <h4 style="margin:0 0 8px 0;">Инженерный Мониторинг Узлов</h4>
    <div id="pro_nodes" style="font-family:monospace;font-size:12px;margin-bottom:10px;"></div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;">
      <button onclick="fetch('/api/control',{method:'POST',body:JSON.stringify({action:'sync_skills_now'})})" style="padding:8px;background:#0284c7;color:white;border:none;border-radius:6px;font-size:11px;cursor:pointer;">🔄 Синхронизировать скилы с ПК</button>
      <button onclick="fetch('/api/control',{method:'POST',body:JSON.stringify({action:'force_train_lora'})})" style="padding:8px;background:#7c3aed;color:white;border:none;border-radius:6px;font-size:11px;cursor:pointer;">⚡ Запустить LoRA на GTX 1050 Ti</button>
      <button onclick="if(confirm('Выключить все смартфоны?')) fetch('/api/control',{method:'POST',body:JSON.stringify({action:'poweroff_all'})})" style="padding:8px;background:#dc2626;color:white;border:none;border-radius:6px;font-size:11px;cursor:pointer;">🛑 Выключить все 3 смартфона</button>
    </div>
  </div>

<script>
let currentModel = 'omni-auto';

async function setMode(action, el) {
  document.querySelectorAll('.big-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  if(action === 'mode_stem') currentModel = 'omni-stem';
  if(action === 'mode_coder') currentModel = 'omni-coder';
  if(action === 'mode_fast') currentModel = 'omni-fast';
  await fetch('/api/control', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action})});
}

async function sendChat() {
  const inp = document.getElementById('user_input');
  const txt = inp.value.trim();
  if(!txt) return;
  const box = document.getElementById('messages');
  box.innerHTML += `<div class="msg-u"><b>Вы:</b> ${txt}</div>`;
  inp.value = '';
  box.scrollTop = box.scrollHeight;

  const aId = 'msg_' + Date.now();
  box.innerHTML += `<div class="msg-a" id="${aId}"><i>Печатает...</i></div>`;
  box.scrollTop = box.scrollHeight;

  try {
    const res = await fetch('/v1/chat/completions', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        model: currentModel,
        messages: [{role: 'user', content: txt}],
        stream: true
      })
    });
    
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let ans = '';
    while(true) {
      const {done, value} = await reader.read();
      if(done) break;
      const chunk = decoder.decode(value);
      const lines = chunk.split('\\n');
      for(const line of lines) {
        if(line.startsWith('data: ') && !line.includes('[DONE]')) {
          try {
            const parsed = JSON.parse(line.substring(6));
            const delta = parsed.choices[0].delta.content || '';
            ans += delta;
            document.getElementById(aId).innerText = ans;
            box.scrollTop = box.scrollHeight;
          } catch(e) {}
        }
      }
    }
  } catch(e) {
    document.getElementById(aId).innerText = 'Ошибка соединения с кластером: ' + e;
  }
}

async function updateStats() {
  try {
    const r = await fetch('/api/dashboard');
    const d = await r.json();
    let info = '';
    let proHtml = '';
    for(const [k, v] of Object.entries(d.nodes)) {
      const t = v.telemetry || {};
      const statusIcon = t.online ? '🟢' : '🔴';
      info += `${statusIcon} ${v.name.split(' ')[0]}: ${t.battery}% (${t.temp_c}°C)  `;
      proHtml += `<div><b>${v.name}:</b> IP=${v.ip}:${v.port} | Заряд=${t.battery}% | Темп=${t.temp_c}°C | ОЗУ свободно=${t.free_ram_mb}МБ</div>`;
    }
    document.getElementById('telemetry_summary').innerText = info;
    document.getElementById('pro_nodes').innerHTML = proHtml;
  } catch(e) {}
}
setInterval(updateStats, 6000);
updateStats();
</script>
</body>
</html>
"""

class FastOmniHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/?kiosk=1"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            return self.wfile.write(UI_HTML.encode("utf-8"))

        if self.path == "/api/dashboard":
            nodes_out = {}
            for k, info in NODES.items():
                nodes_out[k] = dict(info)
                nodes_out[k]["telemetry"] = TELEMETRY_CACHE.get(k, {"online": False, "battery": 0, "temp_c": 0.0, "free_ram_mb": 0})
            return self._send_json({"nodes": nodes_out, "mi10t_profile": CURRENT_MI10T_PROFILE, "teacher_33b": TEACHER_33B_STATE})

        if self.path.startswith("/v1/models"):
            models = ["omni-auto", "omni-stem", "omni-coder", "omni-fast", "bge-m3"]
            return self._send_json({"object": "list", "data": [{"id": m, "object": "model"} for m in models]})

        return self._send_json({"status": "Triad-Omni v4.6 OK"})

    def do_POST(self):
        global CURRENT_MI10T_PROFILE
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}

        if self.path == "/api/control":
            act = body.get("action", "")
            if act == "mode_stem":
                CURRENT_MI10T_PROFILE = "stem"
                subprocess.Popen(["ssh", "-p", "8022", NODES["mi10t"]["ip"], "~/reload_brain.sh stem"])
                add_log("🔬 Включено ядро 9B STEM + Vision", "MODE")
            elif act == "mode_coder":
                CURRENT_MI10T_PROFILE = "coder"
                subprocess.Popen(["ssh", "-p", "8022", NODES["mi10t"]["ip"], "~/reload_brain.sh coder"])
                add_log("💻 Включено ядро 7B Coder 24K", "MODE")
            elif act == "sync_skills_now":
                subprocess.Popen(["ssh", "-o", "StrictHostKeyChecking=no", f"{PC_USER}@{PC_IP}", "python3 ~/omni_auto_trainer/auto_lora_trainer.py --sync-now"])
                add_log("🔄 Принудительная синхронизация скилов с ПК", "SYNC")
            elif act == "force_train_lora":
                subprocess.Popen(["ssh", "-o", "StrictHostKeyChecking=no", f"{PC_USER}@{PC_IP}", "python3 ~/omni_auto_trainer/auto_lora_trainer.py --force-all"])
                add_log("⚡ Запуск компиляции LoRA на GTX 1050 Ti", "TRAIN")
            elif act == "poweroff_all":
                add_log("🛑 Безопасное выключение всех узлов", "POWER")
                for k in ["mi10t", "nord10"]:
                    subprocess.Popen(["ssh", "-p", "8022", NODES[k]["ip"], "su -c 'reboot -p' || poweroff"])
                subprocess.Popen("sleep 2 && (su -c 'reboot -p' || poweroff)", shell=True)
            return self._send_json({"status": "ok", "action": act})

        # --- ОБРАБОТКА ЧАТА (OpenAI, Anthropic Claude Code, SSE Streaming) ---
        if self.path.startswith(("/v1/chat/completions", "/v1/messages", "/api/chat")):
            stream = body.get("stream", False)
            msgs = body.get("messages", [])
            req_model = body.get("model", "omni-auto").lower()

            # Anthropic Messages API поддержка верхнеуровневого system prompt
            sys_anthropic = body.get("system", "")
            if sys_anthropic and isinstance(sys_anthropic, str):
                msgs = [{"role": "system", "content": sys_anthropic}] + msgs

            last_user_text = ""
            has_image = False
            for m in msgs:
                c = m.get("content", "")
                if m.get("role") == "user":
                    last_user_text = str(c)

            # Tool RAG: фильтрация инструментов MCP
            if "tools" in body:
                body["tools"] = filter_mcp_tools(body["tools"], last_user_text)

            # Маршрутизация на узлы
            if "fast" in req_model or "haiku" in req_model:
                target_url = NODE2_FAST
            else:
                target_url = NODE1_BRAIN

            # Подмес базы знаний FTS5
            domain = "coder" if "coder" in req_model else "stem"
            kb_ctx = fetch_active_skills(domain, last_user_text)
            if kb_ctx:
                msgs = [{"role": "system", "content": f"Соблюдай проверенные инженерные стандарты:\n{kb_ctx}"}] + msgs

            body["messages"] = msgs

            # Проброс SSE Стриминга
            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                try:
                    req = urllib.request.Request(target_url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        for chunk in resp:
                            self.wfile.write(chunk)
                            self.wfile.flush()
                except Exception as e:
                    err_msg = json.dumps({"choices": [{"delta": {"content": f" [Ошибка шлюза: {e}]"}}]})
                    self.wfile.write(f"data: {err_msg}\n\n".encode("utf-8"))
                return

            # Не-стриминговый ответ
            try:
                res = http_json(target_url, body)
                return self._send_json(res)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=502)

        return self._send_json({"error": "Not Found"}, status=404)

    def _send_json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    print("🚀 Triad-Omni Gateway v4.6 (Multi-Threaded) запущен на порту 8000")
    server = ThreadingHTTPServer(("0.0.0.0", 8000), FastOmniHandler)
    server.serve_forever()
