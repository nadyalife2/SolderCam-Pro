#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Gateway v4.7  (Redmi Note 4 / Termux)
Запуск: OMNI_TOKEN="..." DEEPSEEK_API_KEY="..." python3 omni_gateway.py
Только stdlib. Опционально: pip install zeroconf (mDNS-анонс).
"""
import os, re, json, math, time, hmac, socket, hashlib, sqlite3, threading, subprocess, urllib.request, urllib.error
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ============================ КОНФИГУРАЦИЯ ============================
OMNI_TOKEN     = os.environ.get("OMNI_TOKEN", "sk-triad")          # СМЕНИТЕ! хранится только в env
DEEPSEEK_KEY   = os.environ.get("DEEPSEEK_API_KEY", "")            # только env, не в коде
DEEPSEEK_URL   = os.environ.get("DEEPSEEK_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
PC_USER        = os.environ.get("PC_USER", "user")
PC_IP          = os.environ.get("PC_IP", "192.168.1.100")

NODES = {
    "mi10t":  {"name": "Xiaomi Mi 10T (Brain 9B-MTP)", "ip": "192.168.1.201", "port": 8080, "role": "Qwen3.5-9B-MTP + 3 LoRA / Vision E4B"},
    "nord10": {"name": "OnePlus Nord N10 (Reflex)",    "ip": "192.168.1.202", "port": 8081, "role": "LFM2.5-8B-A1B + BGE-M3"},
    "note4":  {"name": "Redmi Note 4 (Omni Hub)",      "ip": "192.168.1.203", "port": 8000, "role": "Gateway + SQLite FTS5 + Deck"},
}
BRAIN_BASE  = f"http://{NODES['mi10t']['ip']}:8080"
BRAIN_URL   = f"{BRAIN_BASE}/v1/chat/completions"
FAST_URL    = f"http://{NODES['nord10']['ip']}:8081/v1/chat/completions"
EMBED_URL   = f"http://{NODES['nord10']['ip']}:8082/v1/embeddings"
TEACHER_URL = f"http://{PC_IP}:8090/v1/chat/completions"
BRAIN_MODEL  = os.environ.get("BRAIN_MODEL", "brain")     # имя пресета в router-mode (или игнорируется обычным сервером)
VISION_MODEL = os.environ.get("VISION_MODEL", "vision")   # пресет Gemma 4 E4B + mmproj

ADAPTER_MAP   = {"solder": 0, "reva_android": 1, "esp32": 2}   # порядок --lora при старте brain
ALLOWED_DOMAINS = {"solder", "reva_android", "esp32", "ui_video", "general"}
CLOUD_DOMAINS   = {"solder", "esp32", "ui_video", "general"}   # reva_android НИКОГДА не уходит в облако

# БД только на /data (ext4/f2fs). sdcard — ТОЛЬКО для бэкапов (FUSE ломает WAL).
BASE_DIR = os.path.expanduser("~/omni_hub/data")
DB_FILE  = os.path.join(BASE_DIR, "db", "omni_knowledge.db")
DS_DIR   = os.path.join(BASE_DIR, "datasets")
BACKUP_DIR = "/storage/emulated/0/OmniCluster_Data"   # только rsync-бэкапы
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True); os.makedirs(DS_DIR, exist_ok=True)

BASE_SYSTEM = ("Ты главный ИИ-инженер локального кластера Triad-Omni. Отвечай точно, по делу, "
               "с проверяемым кодом и стандартами. Не выдумывай факты.")  # КОНСТАНТА — не ломать префиксный кэш

# ============================ БД (один conn + RLock) ============================
DB_LOCK = threading.RLock()
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
def db_exec(sql, args=()):
    with DB_LOCK:
        cur = conn.execute(sql, args); conn.commit(); return cur
def db_query(sql, args=()):
    with DB_LOCK:
        return conn.execute(sql, args).fetchall()

for ddl in [
 """CREATE TABLE IF NOT EXISTS skills_meta(id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT, topic TEXT UNIQUE,
    content TEXT, source_folder TEXT, utility_score INTEGER DEFAULT 2, usage_count INTEGER DEFAULT 0, vec_json TEXT, updated_at TEXT)""",
 "CREATE VIRTUAL TABLE IF NOT EXISTS kb_fts USING fts5(domain, topic, content)",
 "CREATE TABLE IF NOT EXISTS articles_vec(slug TEXT PRIMARY KEY, title TEXT, vec_json TEXT, created_at TEXT)",
 "CREATE TABLE IF NOT EXISTS token_stats(domain TEXT PRIMARY KEY, prompt_tokens INTEGER DEFAULT 0, completion_tokens INTEGER DEFAULT 0, requests_count INTEGER DEFAULT 0)",
 "CREATE TABLE IF NOT EXISTS watched_folders(path TEXT PRIMARY KEY, agent_type TEXT, last_sync TEXT)",
 "CREATE TABLE IF NOT EXISTS training_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, level TEXT, event TEXT)",
 "CREATE TABLE IF NOT EXISTS dataset_hashes(sha TEXT PRIMARY KEY, domain TEXT, ts TEXT)",
 "CREATE TABLE IF NOT EXISTS dataset_vec(id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT, vec_json TEXT, ts TEXT)",
]:
    db_exec(ddl)

DEFAULT_FOLDERS = [("~/deepseek-harness/skills","DeepSeek Harness"),("~/.claude","Claude Code CLI"),
                   ("~/.cursor/rules","Cursor / VS Code Rules"),("~/.continue","Continue"),
                   ("~/projects/solder_blog/skills","Solder Blog")]
for p, ag in DEFAULT_FOLDERS:
    db_exec("INSERT OR IGNORE INTO watched_folders VALUES (?,?, 'Ожидание')", (p, ag))

CORE_SKILLS = [
 ("reva_android","Ghidra_JNI_Bridge","Первый аргумент JNI-функций всегда JNIEnv* (X0 в ARM64), второй — jobject/jclass (X1). Ищи вызовы RegisterNatives для восстановления JNINativeMethod (name, signature, fnPtr)."),
 ("reva_android","ARM64_Bootloader_ABI","AAPCS64: X0-X7 аргументы, X8 адрес возврата сложных структур, SP выровнен на 16 байт. Проверки подписи AVB 2.0 — по строкам avb_slot_verify."),
 ("solder","Solder_Metallurgy_GOST","ПОС-61 (ГОСТ 21930-76): Sn61/Pb39, солидус 183°C, ликвидус 190°C. SAC305: 217-220°C. Контроль по IPC-A-610 Class 2/3."),
 ("esp32","ESP32_S3_Hardware_Rules","ESP32-S3 Octal PSRAM/Flash: GPIO33-37 заняты. I2S DMA-буферы во внутренней SRAM (MALLOC_CAP_DMA), кадры камеры в PSRAM (MALLOC_CAP_SPIRAM)."),
 ("ui_video","HTMLmark_2.0_UI_Standard","Тёмная палитра: фон #0b1120, карточки #161f33, акцент #f59e0b. Адаптивный CSS Grid minmax(300px,1fr), Vanilla JS без фреймворков."),
]
for dom, top, cnt in CORE_SKILLS:
    if not db_query("SELECT id FROM skills_meta WHERE topic=?", (top,)):
        db_exec("INSERT INTO skills_meta(domain,topic,content,source_folder,utility_score,updated_at) VALUES (?,?,?,?,10,?)",
                (dom, top, cnt, "Built-in Standard", datetime.now().strftime("%Y-%m-%d %H:%M")))
        db_exec("INSERT INTO kb_fts(domain,topic,content) VALUES (?,?,?)", (dom, top, cnt))

# ============================ СОСТОЯНИЕ ============================
TELEMETRY = {}            # push-телеметрия узлов (без SSH-pull)
LAST_ALERT = {"beep": None, "ts": 0}
TEACHER_STATE = "OFFLINE"
_cur_domain = None
_last_kind = None
_dom_lock = threading.Lock()
STATS_BUF = {}
_stats_lock = threading.Lock()

def add_log(msg, level="INFO", beep=None):
    db_exec("INSERT INTO training_logs(ts,level,event) VALUES (?,?,?)",
            (datetime.now().strftime("%H:%M:%S"), level, msg))
    db_exec("DELETE FROM training_logs WHERE id NOT IN (SELECT id FROM training_logs ORDER BY id DESC LIMIT 200)")
    if beep:
        LAST_ALERT.update({"beep": beep, "ts": time.time()})
        subprocess.Popen("su -c 'input keyevent 224' 2>/dev/null", shell=True)

def http_json(url, payload, headers=None, timeout=120):
    hdrs = {"Content-Type": "application/json"}
    if headers: hdrs.update(headers)
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

# ============================ ГОРЯЧИЕ LoRA-ДОМЕНЫ ============================
def set_domain_adapter(domain):
    """Мгновенная смена адаптера без перезагрузки + инвалидация KV (слот erase)."""
    global _cur_domain
    if domain not in ADAPTER_MAP:
        return
    with _dom_lock:
        if domain == _cur_domain:
            return
        idx = ADAPTER_MAP[domain]
        scales = [{"id": i, "scale": 1.0 if i == idx else 0.0} for i in ADAPTER_MAP.values()]
        try:
            http_json(f"{BRAIN_BASE}/lora-adapters", scales, timeout=3)
            urllib.request.urlopen(urllib.request.Request(
                f"{BRAIN_BASE}/slots/0?action=erase", method="POST"), timeout=3).read()
            _cur_domain = domain
            add_log(f"🎛 Домен [{domain}]: адаптер #{idx} активирован (KV сброшен)", "MODE")
        except Exception as e:
            add_log(f"⚠️ Смена адаптера не удалась: {e}", "WARN")

# ============================ ЭСКАЛАЦИЯ (On-Policy Distillation) ============================
REFUSAL_MARKERS = ("i cannot assist", "i can't assist", "i'm unable to", "не могу помочь", "я не могу помочь с")
def escalate(domain, prompt, bad_reply, error_log):
    msgs = [
        {"role": "system", "content": "Ты senior-инженер. Исправь ответ строго по логу ошибки верификации. Верни только исправленный результат."},
        {"role": "user", "content": f"Задача:\n{prompt}\n\nПредыдущий ответ:\n{bad_reply}\n\nОшибка верификации:\n{error_log[:4000]}"},
    ]
    if domain in CLOUD_DOMAINS and DEEPSEEK_KEY:
        payload = {"model": DEEPSEEK_MODEL, "messages": msgs, "max_tokens": 4096,
                   "temperature": 0.3, "reasoning_effort": 60}
        hdrs = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        try:
            try:
                res = http_json(DEEPSEEK_URL, payload, headers=hdrs, timeout=180)
            except urllib.error.HTTPError as e:
                if e.code == 400:                      # API может не знать reasoning_effort
                    payload.pop("reasoning_effort", None)
                    res = http_json(DEEPSEEK_URL, payload, headers=hdrs, timeout=180)
                else:
                    raise
            txt = res["choices"][0]["message"]["content"] or ""
            if not any(m in txt.lower() for m in REFUSAL_MARKERS):
                return txt, "flash"
            add_log("⚠️ Flash отказал → локальный учитель", "WARN")
        except Exception as e:
            add_log(f"⚠️ Flash недоступен: {e} → локальный учитель", "WARN")
    # reva_android / приватное / отказ → локальный MoE-учитель на ПК
    res = http_json(TEACHER_URL, {"messages": msgs, "max_tokens": 4096, "temperature": 0.3}, timeout=600)
    return res["choices"][0]["message"]["content"], "local_teacher"

# ============================ ВЕКТОРЫ / ДОМЕНЫ / ДАТАСЕТ ============================
def get_embedding(text, timeout=4):
    try:
        res = http_json(EMBED_URL, {"input": text[:1500]}, timeout=timeout)
        if res.get("data"): return res["data"][0]["embedding"]
    except Exception:
        pass
    return None

def cosine_sim(v1, v2):
    if not v1 or not v2 or len(v1) != len(v2): return 0.0
    dot = sum(a*b for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(a*a for a in v1)); n2 = math.sqrt(sum(b*b for b in v2))
    return dot/(n1*n2) if n1 and n2 else 0.0

def dynamic_detect_domain(text):
    t = text.lower()
    if any(w in t for w in ["ui","css","html","widget","калькулятор","верстк","manim","remotion","ffmpeg","видео"]): return "ui_video"
    if any(w in t for w in ["ghidra","reva","jni","smali","fastboot","edl","modemst","abl.elf","android studio","gradle","logcat"]): return "reva_android"
    if any(w in t for w in ["esp32","freertos","i2s","ov3660","inmp441","max98357","gpio","esp-idf","platformio"]): return "esp32"
    if any(w in t for w in ["припой","флюс","пайк","гост","ipc","bga","олово","канифоль","температур","смачиваем"]): return "solder"
    try:
        p = f"Категории: {sorted(ALLOWED_DOMAINS)}. Запрос: '{text[:180]}'. Ответь ОДНИМ словом-тегом из списка:"
        res = http_json(FAST_URL, {"messages":[{"role":"user","content":p}], "max_tokens":12, "temperature":0.1}, timeout=4)
        tag = "".join(c for c in res["choices"][0]["message"]["content"].strip().lower() if c.isalnum() or c=="_")[:20]
        return tag if tag in ALLOWED_DOMAINS else "general"
    except Exception:
        return "general"

def fetch_active_skills(domain, query_text):
    words = [w for w in "".join(c if c.isalnum() else " " for c in query_text).split() if len(w) > 3]
    topics = []
    if words:
        try:
            topics = [r[0] for r in db_query("SELECT topic FROM kb_fts WHERE kb_fts MATCH ? LIMIT 3", (" OR ".join(words[:8]),))]
        except Exception:
            pass
    ph = ",".join(["?"]*len(topics)) if topics else "''"
    rows = db_query(f"SELECT id,topic,content FROM skills_meta WHERE (domain=? OR topic IN ({ph})) AND utility_score>-2 ORDER BY utility_score DESC LIMIT 4",
                    tuple([domain]+topics))
    for r in rows:
        db_exec("UPDATE skills_meta SET usage_count=usage_count+1 WHERE id=?", (r[0],))
    return "\n".join(f"• [{r[1]}]: {r[2]}" for r in rows)

def save_training_pair(domain, prompt, reply, source="verified"):
    """В датасет — только верифицированные пары. vec НЕ пишется в jsonl."""
    if domain not in ALLOWED_DOMAINS: domain = "general"
    if len(prompt.strip()) < 15 or len(reply.strip()) < 60: return False
    sha = hashlib.sha256((prompt.strip()+"\n"+reply.strip()).encode("utf-8")).hexdigest()
    if db_query("SELECT sha FROM dataset_hashes WHERE sha=?", (sha,)): return False
    # best-effort семантический дедуп по отдельной таблице (не блокирует запись надолго)
    vec = get_embedding(prompt[:500]+"\n"+reply[:500], timeout=3)
    if vec:
        for (vj,) in db_query("SELECT vec_json FROM dataset_vec WHERE domain=? ORDER BY id DESC LIMIT 30", (domain,)):
            try:
                if cosine_sim(vec, json.loads(vj)) > 0.92: return False
            except Exception:
                pass
    ds_path = os.path.join(DS_DIR, f"sft_{domain}.jsonl")
    record = {"messages":[{"role":"user","content":prompt},{"role":"assistant","content":reply}]}
    with open(ds_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False)+"\n")
    db_exec("INSERT OR IGNORE INTO dataset_hashes VALUES (?,?,?)", (sha, domain, datetime.now().isoformat()))
    if vec:
        db_exec("INSERT INTO dataset_vec(domain,vec_json,ts) VALUES (?,?,?)", (domain, json.dumps(vec), datetime.now().isoformat()))
    add_log(f"📥 Верифицированная пара → sft_{domain}.jsonl (источник: {source})")
    return True

def log_tokens(domain, usage, prompt_text, reply_text):
    p = usage.get("prompt_tokens") or max(1, len(prompt_text)//4)
    c = usage.get("completion_tokens") or max(1, len(reply_text)//4)
    with _stats_lock:
        b = STATS_BUF.setdefault(domain, [0, 0, 0])
        b[0] += p; b[1] += c; b[2] += 1

def stats_flusher():
    while True:
        time.sleep(45)
        with _stats_lock:
            buf = dict(STATS_BUF); STATS_BUF.clear()
        for dom, (p, c, n) in buf.items():
            db_exec("INSERT OR IGNORE INTO token_stats(domain,prompt_tokens,completion_tokens,requests_count) VALUES (?,0,0,0)", (dom,))
            db_exec("UPDATE token_stats SET prompt_tokens=prompt_tokens+?, completion_tokens=completion_tokens+?, requests_count=requests_count+? WHERE domain=?",
                    (p, c, n, dom))

# ============================ ТЕЛЕМЕТРИЯ (push + локальная) ============================
def local_telemetry_loop():
    while True:
        try:
            def rd(p, d="0"):
                try: return open(p).read().strip()
                except Exception: return d
            TELEMETRY["note4"] = {
                "online": True, "ts": time.time(),
                "battery": int(rd("/sys/class/power_supply/battery/capacity", "50")),
                "temp_c": round(int(rd("/sys/class/power_supply/battery/temp", "300"))/10.0, 1),
                "free_ram_mb": int([l for l in open("/proc/meminfo") if "MemAvailable" in l][0].split()[1])//1024,
                "mac": rd("/sys/class/net/wlan0/address", "00:00:00:00:00:00"),
                "profile": "hub",
            }
        except Exception:
            pass
        time.sleep(10)

def teacher_watch_loop():
    global TEACHER_STATE
    while True:
        try:
            with urllib.request.urlopen(f"http://{PC_IP}:8090/health", timeout=2) as r:
                TEACHER_STATE = "ONLINE" if r.status == 200 else "OFFLINE"
        except Exception:
            TEACHER_STATE = "OFFLINE"
        time.sleep(15)

def start_mdns():
    try:
        from zeroconf import Zeroconf, ServiceInfo
        ip = NODES["note4"]["ip"]
        info = ServiceInfo("_omni._tcp.local.", "omni-hub._omni._tcp.local.",
                           addresses=[socket.inet_aton(ip)], port=8000,
                           properties={"v": "4.7"}, server="omni-hub.local.")
        Zeroconf().register_service(info)
        add_log("📡 mDNS: omni-hub.local анонсирован", "NET")
    except Exception:
        pass   # zeroconf не установлен — не критично

# ============================ ПРОТОКОЛЫ: конвертация ============================
THINK_RE = re.compile(r"<think>.*?</think>", re.S)
def strip_think(s): return THINK_RE.sub("", s or "").strip()

def anthropic_to_oai(body):
    """Anthropic Messages -> OpenAI chat. Учитывает system/tools/tool_use/tool_result, вырезает thinking."""
    sys_parts = []
    s = body.get("system")
    if isinstance(s, str): sys_parts.append(s)
    elif isinstance(s, list):
        sys_parts += [p.get("text", "") for p in s if isinstance(p, dict) and p.get("type") == "text"]
    msgs = []
    for m in body.get("messages", []):
        role, c = m.get("role"), m.get("content")
        if isinstance(c, str):
            msgs.append({"role": role, "content": strip_think(c) if role == "assistant" else c}); continue
        texts, images, tool_calls, tool_results = [], [], [], []
        for p in c or []:
            t = p.get("type")
            if t == "text": texts.append(p.get("text", ""))
            elif t == "image":
                src = p.get("source", {})
                images.append({"type": "image_url", "image_url": {"url": f"data:{src.get('media_type','image/jpeg')};base64,{src.get('data','')}"}})
            elif t == "image_url": images.append(p)
            elif t == "tool_use":
                tool_calls.append({"id": p.get("id"), "type": "function",
                                   "function": {"name": p.get("name"), "arguments": json.dumps(p.get("input", {}), ensure_ascii=False)}})
            elif t == "tool_result":
                cont = p.get("content", "")
                if isinstance(cont, list): cont = "".join(x.get("text", "") for x in cont if isinstance(x, dict))
                tool_results.append({"role": "tool", "tool_call_id": p.get("tool_use_id"), "content": str(cont)})
            # thinking / redacted_thinking — пропускаем
        if role == "assistant":
            am = {"role": "assistant", "content": strip_think("\n".join(texts)) or None}
            if tool_calls: am["tool_calls"] = tool_calls
            msgs.append(am)
        else:
            msgs.extend(tool_results)
            if texts or images:
                if images:
                    parts = ([{"type": "text", "text": "\n".join(texts)}] if texts else []) + images
                    msgs.append({"role": "user", "content": parts})
                else:
                    msgs.append({"role": "user", "content": "\n".join(texts)})
    tools = None
    if body.get("tools"):
        tools = [{"type": "function", "function": {"name": t.get("name"), "description": t.get("description", ""),
                  "parameters": t.get("input_schema", {"type": "object", "properties": {}})}} for t in body["tools"]]
    tc, oai_tc = body.get("tool_choice"), None
    if isinstance(tc, dict):
        if tc.get("type") == "auto": oai_tc = "auto"
        elif tc.get("type") == "any": oai_tc = "required"
        elif tc.get("type") == "tool": oai_tc = {"type": "function", "function": {"name": tc.get("name")}}
    return msgs, "\n\n".join(sys_parts), tools, oai_tc

def oai_clean_messages(msgs):
    out = []
    for m in msgs:
        m = dict(m)
        if m.get("role") == "assistant" and isinstance(m.get("content"), str):
            m["content"] = strip_think(m["content"])
        out.append(m)
    return out

def last_user_and_image(msgs):
    text, has_img = "", False
    for m in msgs:
        c = m.get("content")
        if isinstance(c, list):
            for p in c:
                if p.get("type") == "image_url": has_img = True
                if p.get("type") == "text" and m.get("role") == "user": text = p.get("text", "")
        elif m.get("role") == "user" and isinstance(c, str):
            text = c
    return text, has_img

# ============================ SSE-РЕТРАНСЛЯЦИЯ ============================
class StreamRelay:
    """OpenAI SSE upstream -> клиент в формате openai / anthropic / ollama.
    Heartbeat отдельным потоком, отмена upstream при обрыве клиента."""
    def __init__(self, handler, mode):
        self.h, self.mode = handler, mode
        self.wlock = threading.Lock()
        self.stop = threading.Event()
        self.reply_parts = []
        self.usage = {}
        # anthropic state
        self.started = False; self.text_open = False; self.next_idx = 0
        self.tools = {}; self.finish = None; self.msg_id = f"msg_{int(time.time()*1000)}"

    def _write(self, data):
        with self.wlock:
            self.h.wfile.write(data); self.h.wfile.flush()

    def emit(self, obj):
        if self.mode == "ollama":
            self._write((json.dumps(obj, ensure_ascii=False)+"\n").encode())
        else:
            self._write(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode())

    def emit_event(self, event, obj):
        self._write(f"event: {event}\ndata: {json.dumps(obj, ensure_ascii=False)}\n\n".encode())

    def heartbeat(self):
        while not self.stop.wait(12):
            if self.mode == "ollama": continue
            try: self._write(b": ping\n\n")
            except Exception: self.stop.set(); break

    def anthropic_chunk(self, chunk):
        if not self.started:
            self.emit_event("message_start", {"type": "message_start", "message": {
                "id": self.msg_id, "type": "message", "role": "assistant", "model": "triad-omni",
                "content": [], "stop_reason": None,
                "usage": {"input_tokens": self.usage.get("prompt_tokens", 0), "output_tokens": 0}}})
            self.started = True
        ch = (chunk.get("choices") or [{}])[0]
        delta = ch.get("delta") or {}
        if ch.get("finish_reason"): self.finish = ch["finish_reason"]
        txt = delta.get("content")
        if txt:
            self.reply_parts.append(txt)
            if not self.text_open:
                self.emit_event("content_block_start", {"type": "content_block_start", "index": self.next_idx,
                                                        "content_block": {"type": "text", "text": ""}})
                self.text_open = True
            self.emit_event("content_block_delta", {"type": "content_block_delta", "index": self.next_idx,
                                                    "delta": {"type": "text_delta", "text": txt}})
        for tc in delta.get("tool_calls") or []:
            i = tc.get("index", 0)
            if i not in self.tools:
                if self.text_open:
                    self.emit_event("content_block_stop", {"type": "content_block_stop", "index": self.next_idx})
                    self.next_idx += 1; self.text_open = False
                fn = tc.get("function") or {}
                self.tools[i] = {"idx": self.next_idx, "id": tc.get("id") or f"toolu_{i}", "name": fn.get("name") or ""}
                self.emit_event("content_block_start", {"type": "content_block_start", "index": self.next_idx,
                    "content_block": {"type": "tool_use", "id": self.tools[i]["id"], "name": self.tools[i]["name"], "input": {}}})
                self.next_idx += 1
            args = (tc.get("function") or {}).get("arguments")
            if args:
                self.emit_event("content_block_delta", {"type": "content_block_delta", "index": self.tools[i]["idx"],
                                                        "delta": {"type": "input_json_delta", "partial_json": args}})
        if chunk.get("usage"): self.usage = chunk["usage"]

    def anthropic_finish(self):
        if not self.started: self.anthropic_chunk({})
        if self.text_open:
            self.emit_event("content_block_stop", {"type": "content_block_stop", "index": self.next_idx})
        for t in self.tools.values():
            self.emit_event("content_block_stop", {"type": "content_block_stop", "index": t["idx"]})
        stop = "tool_use" if self.tools else ("max_tokens" if self.finish == "length" else "end_turn")
        self.emit_event("message_delta", {"type": "message_delta",
            "delta": {"stop_reason": stop, "stop_sequence": None},
            "usage": {"output_tokens": self.usage.get("completion_tokens", 0)}})
        self.emit_event("message_stop", {"type": "message_stop"})

    def run(self, url, payload):
        hdrs = {"Content-Type": "application/json", "Accept": "text/event-stream"}
        if url == DEEPSEEK_URL: hdrs["Authorization"] = f"Bearer {DEEPSEEK_KEY}"
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=hdrs)
        hb = threading.Thread(target=self.heartbeat, daemon=True); hb.start()
        up = None
        try:
            up = urllib.request.urlopen(req, timeout=300)   # таймаут на КАЖДОЕ чтение (prefill может молчать)
            for raw in up:
                if self.stop.is_set(): break
                line = raw.decode("utf-8", "ignore").strip()
                if not line.startswith("data:"): continue
                data = line[5:].strip()
                if data == "[DONE]":
                    if self.mode == "openai": self._write(b"data: [DONE]\n\n")
                    break
                try: chunk = json.loads(data)
                except Exception: continue
                if self.mode == "openai":
                    self._write(f"data: {data}\n\n".encode())
                    d = (chunk.get("choices") or [{}])[0].get("delta") or {}
                    if d.get("content"): self.reply_parts.append(d["content"])
                    if chunk.get("usage"): self.usage = chunk["usage"]
                elif self.mode == "anthropic":
                    self.anthropic_chunk(chunk)
                elif self.mode == "ollama":
                    d = (chunk.get("choices") or [{}])[0].get("delta") or {}
                    if d.get("content"):
                        self.reply_parts.append(d["content"])
                        self.emit({"model": "triad-omni", "message": {"role": "assistant", "content": d["content"]}, "done": False})
                    if chunk.get("usage"): self.usage = chunk["usage"]
            if self.mode == "anthropic": self.anthropic_finish()
            if self.mode == "ollama":
                self.emit({"model": "triad-omni", "message": {"role": "assistant", "content": ""}, "done": True,
                           "eval_count": self.usage.get("completion_tokens", 0)})
        except (BrokenPipeError, ConnectionResetError):
            self.stop.set()   # клиент ушёл — отменяем генерацию
        except Exception as e:
            try:
                if self.mode == "anthropic": self.emit_event("error", {"type": "error", "error": {"message": str(e)}})
                else: self.emit({"error": str(e)})
            except Exception:
                pass
        finally:
            self.stop.set()
            if up:
                try: up.close()
                except Exception: pass
        return "".join(self.reply_parts), self.usage

# ============================ DASHBOARD ============================
DASHBOARD_HTML = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Triad-Omni v4.7 Control Deck</title><style>
:root{--bg:#0b1120;--card:#161f33;--accent:#f59e0b;--blue:#38bdf8;--green:#22c55e;--red:#ef4444;--text:#f8fafc}
*{box-sizing:border-box}body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);margin:0;padding:14px}
.top-bar{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #334155;padding-bottom:12px;margin-bottom:14px;flex-wrap:wrap;gap:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px;margin-bottom:16px}
.card{background:var(--card);border-radius:12px;padding:14px;border:1px solid #334155}
.badge{padding:4px 10px;border-radius:99px;font-size:12px;font-weight:bold}
.on{background:rgba(34,197,94,.2);color:var(--green)}.off{background:rgba(239,68,68,.2);color:var(--red)}
.hot{background:rgba(239,68,68,.35);color:#fca5a5;animation:blink 1s infinite}@keyframes blink{50%{opacity:.4}}
.stat-row{display:flex;justify-content:space-between;margin:6px 0;font-size:13px;border-bottom:1px dashed #26334d;padding-bottom:4px}
.btn-deck{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;margin-bottom:16px}
button{background:var(--blue);color:#0b1120;border:none;padding:11px 14px;border-radius:10px;font-weight:800;font-size:13px;cursor:pointer}
button:active{transform:scale(.97)}button.warn{background:var(--accent)}button.purple{background:#a855f7;color:#fff}
button.danger{background:var(--red);color:#fff}button.success{background:var(--green);color:#052e16}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:8px;border-bottom:1px solid #26334d}
input,textarea{background:#0b1120;color:#fff;border:1px solid #475569;padding:8px;border-radius:6px;width:100%;margin-bottom:6px}
code{background:#0b1120;padding:2px 6px;border-radius:4px;color:var(--accent);font-family:monospace}
body.kiosk .pc-only{display:none!important}body.kiosk button{padding:16px 12px;font-size:15px}
</style></head><body>
<div class="top-bar"><div>
<h2 style="margin:0">⚡ Triad-Omni v4.7 <span id="domain_badge" class="badge on">...</span></h2>
<small>Шлюз: <code>omni-hub.local:8000</code> | Учитель (ПК): <b id="teacher_stat">...</b> | БД: <code id="storage_path"></code></small>
</div><div><button onclick="toggleKiosk()">📱 ПК / Пульт</button><button onclick="loadStats()">🔄 Обновить</button></div></div>
<div class="btn-deck">
<button class="success" onclick="setDomain('solder')">🔬 ДОМЕН: ПАЙКА</button>
<button class="warn" onclick="setDomain('reva_android')">💻 ДОМЕН: GHIDRA / РЕВЕРС</button>
<button onclick="setDomain('esp32')">🔌 ДОМЕН: ESP32</button>
<button onclick="setDomain('ui_video')">🎨 ДОМЕН: UI / ВИДЕО</button>
<button onclick="ctrl('sync_skills_now')">🔄 СИНХРОНИЗИРОВАТЬ СКИЛЫ</button>
<button class="purple" onclick="ctrl('force_train_lora')">⚡ ТРЕНИРОВКА / ПОДГОТОВКА COLAB</button>
<button onclick="ctrl('toggle_teacher')">🎓 УЧИТЕЛЬ MoE (ПК)</button>
<button class="warn pc-only" onclick="ctrl('prune_skills')">🧹 ЧИСТКА БАЗЫ</button>
<button class="danger" onclick="if(confirm('Бэкап и выключение всех смартфонов?'))ctrl('poweroff_all')">🛑 ВЫКЛЮЧИТЬ КЛАСТЕР</button>
</div>
<div class="grid" id="nodes_grid">Загрузка...</div>
<div class="grid">
<div class="card"><h3 style="margin-top:0">📊 Домены и корзины LoRA</h3>
<table id="domains_table"><thead><tr><th>Домен</th><th>Запросов</th><th>Токены In/Out</th><th>Пар</th><th></th></tr></thead><tbody></tbody></table></div>
<div class="card"><h3 style="margin-top:0">📡 Журнал</h3><div id="logs_box" style="max-height:210px;overflow-y:auto;font-family:monospace;font-size:12px"></div></div>
</div>
<div class="grid pc-only">
<div class="card"><h3 style="margin-top:0">📂 Папки скилов на ПК</h3>
<div style="display:flex;gap:6px;margin-bottom:10px"><input id="new_folder" placeholder="~/my_project/skills" style="margin:0"><button onclick="addFolder()" style="white-space:nowrap">+ Папка</button></div>
<table id="folders_table"><thead><tr><th>Путь</th><th>Агент</th><th>Синхр.</th></tr></thead><tbody></tbody></table></div>
<div class="card"><h3 style="margin-top:0">➕ One-Click Learn</h3>
<input id="learn_prompt" placeholder="Тема / вопрос"><textarea id="learn_reply" rows="3" placeholder="Эталонный ответ..."></textarea>
<button class="success" onclick="manualLearn()">💾 В FTS5 + корзину LoRA</button></div>
</div>
<div class="card pc-only"><h3 style="margin-top:0">🧬 Навыки (Utility Score)</h3>
<table id="skills_table"><thead><tr><th>Домен</th><th>Навык</th><th>Источник</th><th>Вызовов</th><th>Вес</th><th>Оценка</th></tr></thead><tbody></tbody></table></div>
<script>
const qs=new URLSearchParams(location.search);
let TOKEN=qs.get('token')||localStorage.getItem('omni_token')||'';
if(!TOKEN){TOKEN=prompt('OMNI_TOKEN:')||'';localStorage.setItem('omni_token',TOKEN);}
if(qs.get('kiosk')==='1'||location.hostname==='127.0.0.1')document.body.classList.add('kiosk');
function toggleKiosk(){document.body.classList.toggle('kiosk')}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function H(){return{'Content-Type':'application/json','X-Omni-Token':TOKEN}}
function playBeep(t){try{const c=new(window.AudioContext||window.webkitAudioContext)(),o=c.createOscillator();o.type=t==='alarm'?'sawtooth':'sine';o.frequency.value=t==='alarm'?880:520;o.connect(c.destination);o.start();o.stop(c.currentTime+(t==='alarm'?.45:.15))}catch(e){}}
let lastAlertTs=0;
async function loadStats(){try{
const r=await fetch('/api/dashboard',{headers:H()});if(r.status===401){TOKEN=prompt('OMNI_TOKEN:')||'';localStorage.setItem('omni_token',TOKEN);return}
const d=await r.json();
document.getElementById('storage_path').innerText=esc(d.storage_path);
document.getElementById('domain_badge').innerText=esc((d.current_domain||'auto').toUpperCase());
document.getElementById('teacher_stat').innerText=esc(d.teacher);
if(d.alert&&d.alert.ts>lastAlertTs){lastAlertTs=d.alert.ts;playBeep(d.alert.beep)}
let nh='';for(const[k,n]of Object.entries(d.nodes)){const t=n.telemetry;
const tb=t.temp_c>=45?`<span class="badge hot">🔥 ${esc(t.temp_c)}°C</span>`:`<b>${esc(t.temp_c)}°C</b>`;
nh+=`<div class="card"><div style="display:flex;justify-content:space-between"><b>${esc(n.name)}</b><span class="badge ${t.online?'on':'off'}">${t.online?'ONLINE':'OFFLINE'}</span></div>
<div class="stat-row"><span>Роль:</span><span>${esc(n.role)}</span></div>
<div class="stat-row"><span>IP:</span><code>${esc(n.ip)}:${esc(n.port)}</code></div>
<div class="stat-row"><span>Заряд / Темп.:</span><span>🔋 <b>${esc(t.battery)}%</b> | ${tb}</span></div>
<div class="stat-row"><span>Свободно ОЗУ:</span><b>${esc(t.free_ram_mb)} МБ</b></div></div>`}
document.getElementById('nodes_grid').innerHTML=nh;
let dh='';for(const dom of d.domains){dh+=`<tr><td><code>${esc(dom.domain)}</code></td><td>${esc(dom.requests)}</td><td>${esc(dom.prompt_tokens)} / <b>${esc(dom.completion_tokens)}</b></td><td><b>${esc(dom.samples_count)}</b></td><td><button style="padding:4px 8px;font-size:11px" onclick="ctrl('train_domain','${esc(dom.domain)}')">Обучить</button></td></tr>`}
document.querySelector('#domains_table tbody').innerHTML=dh||'<tr><td colspan="5">Нет данных</td></tr>';
document.getElementById('logs_box').innerHTML=d.logs.map(l=>`<div style="margin-bottom:4px"><span style="color:#64748b">[${esc(l.ts)}]</span> <b>${esc(l.level)}:</b> ${esc(l.event)}</div>`).join('');
document.querySelector('#folders_table tbody').innerHTML=d.folders.map(f=>`<tr><td><code>${esc(f.path)}</code></td><td>${esc(f.agent)}</td><td>${esc(f.last_sync)}</td></tr>`).join('');
document.querySelector('#skills_table tbody').innerHTML=d.skills.map(s=>`<tr><td><code>${esc(s.domain)}</code></td><td><b>${esc(s.topic)}</b><br><small style="color:#94a3b8">${esc(s.preview)}</small></td><td><code>${esc(s.source)}</code></td><td>${esc(s.usage)}</td><td><b>${esc(s.score)}</b></td><td><button style="padding:4px 8px" onclick="voteSkill(${s.id},1)">👍</button> <button class="danger" style="padding:4px 8px" onclick="voteSkill(${s.id},-5)">🗑️</button></td></tr>`).join('');
}catch(e){}}
async function ctrl(action,domain=''){await fetch('/api/control',{method:'POST',headers:H(),body:JSON.stringify({action,domain})});setTimeout(loadStats,600)}
async function setDomain(d){await fetch('/api/control',{method:'POST',headers:H(),body:JSON.stringify({action:'set_domain',domain:d})});setTimeout(loadStats,400)}
async function addFolder(){const p=document.getElementById('new_folder').value.trim();if(!p)return;await fetch('/api/control',{method:'POST',headers:H(),body:JSON.stringify({action:'add_folder',path:p})});document.getElementById('new_folder').value='';loadStats()}
async function voteSkill(id,delta){await fetch('/api/control',{method:'POST',headers:H(),body:JSON.stringify({action:'vote_skill',id,delta})});loadStats()}
async function manualLearn(){const p=document.getElementById('learn_prompt').value.trim(),r=document.getElementById('learn_reply').value.trim();if(!p||!r)return;await fetch('/v1/learn',{method:'POST',headers:H(),body:JSON.stringify({prompt:p,response:r,fact_summary:r})});document.getElementById('learn_prompt').value='';document.getElementById('learn_reply').value='';loadStats()}
loadStats();setInterval(loadStats,10000);
</script></body></html>"""

# ============================ HANDLER ============================
class OmniGatewayHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass

    def _authorized(self):
        tok = self.headers.get("X-Omni-Token", "")
        if not tok:
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer "): tok = auth[7:]
        return hmac.compare_digest(tok, OMNI_TOKEN)

    def _send(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204); self.send_header("Content-Length", "0"); self.end_headers()

    # ---------------- GET ----------------
    def do_GET(self):
        try:
            if self.path == "/" or self.path.startswith("/?"):
                data = DASHBOARD_HTML.encode("utf-8")
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data))); self.end_headers()
                return self.wfile.write(data)
            if not self._authorized():
                return self._send({"error": "unauthorized"}, 401)

            if self.path == "/api/dashboard":
                nodes_out = {}
                for k, info in NODES.items():
                    t = TELEMETRY.get(k, {})
                    online = t.get("online", False) and (time.time() - t.get("ts", 0) < 30)
                    nodes_out[k] = dict(info)
                    nodes_out[k]["telemetry"] = {**{"battery":0,"temp_c":0.0,"free_ram_mb":0,"mac":"OFFLINE","profile":"offline"}, **t, "online": online}
                doms = set(ALLOWED_DOMAINS)
                for f in os.listdir(DS_DIR):
                    if f.startswith("sft_") and f.endswith(".jsonl"): doms.add(f[4:-6])
                domains_list = []
                for dom in sorted(doms):
                    row = db_query("SELECT prompt_tokens,completion_tokens,requests_count FROM token_stats WHERE domain=?", (dom,))
                    p, c, n = row[0] if row else (0, 0, 0)
                    dsp = os.path.join(DS_DIR, f"sft_{dom}.jsonl")
                    cnt = sum(1 for _ in open(dsp, encoding="utf-8")) if os.path.exists(dsp) else 0
                    domains_list.append({"domain": dom, "prompt_tokens": p, "completion_tokens": c, "requests": n, "samples_count": cnt})
                folders = [{"path": r[0], "agent": r[1], "last_sync": r[2]} for r in db_query("SELECT path,agent_type,last_sync FROM watched_folders")]
                skills = [{"id": r[0], "domain": r[1], "topic": r[2], "preview": r[3][:110]+("..." if len(r[3])>110 else ""),
                           "source": r[4], "score": r[5], "usage": r[6]}
                          for r in db_query("SELECT id,domain,topic,content,source_folder,utility_score,usage_count FROM skills_meta WHERE utility_score>-3 ORDER BY utility_score DESC LIMIT 60")]
                logs = [{"ts": r[0], "level": r[1], "event": r[2]} for r in db_query("SELECT ts,level,event FROM training_logs ORDER BY id DESC LIMIT 20")]
                return self._send({"storage_path": BASE_DIR, "current_domain": _cur_domain or "auto",
                                   "teacher": TEACHER_STATE, "alert": LAST_ALERT, "nodes": nodes_out,
                                   "domains": domains_list, "folders": folders, "skills": skills, "logs": logs})

            if self.path == "/v1/watched_folders":
                return self._send({"folders": [r[0] for r in db_query("SELECT path FROM watched_folders")]})
            if self.path == "/v1/training_status":
                stats = {}
                for f in os.listdir(DS_DIR):
                    if f.startswith("sft_") and f.endswith(".jsonl"):
                        stats[f[4:-6]] = sum(1 for _ in open(os.path.join(DS_DIR, f), encoding="utf-8"))
                return self._send(stats)
            if self.path.startswith("/v1/models"):
                models = ["omni-auto","omni-fast","omni-brain","omni-vision","omni-teacher","omni-deep",
                          "omni-solder","omni-reva","omni-esp32","omni-ui-video","bge-m3"]
                return self._send({"object": "list", "data": [{"id": m, "object": "model"} for m in models]})
            if self.path.startswith("/api/tags"):
                models = ["omni-auto","omni-fast","omni-brain","omni-vision","omni-teacher","omni-deep"]
                return self._send({"models": [{"name": m, "model": m} for m in models]})
            return self._send({"status": "Triad-Omni v4.7 Online"})
        except Exception as e:
            try: self._send({"error": str(e)}, 500)
            except Exception: pass

    # ---------------- POST ----------------
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            except Exception:
                return self._send({"error": "bad json"}, 400)
            if not self._authorized():
                return self._send({"error": "unauthorized"}, 401)

            # --- Пульт управления ---
            if self.path == "/api/control":
                act, dom = body.get("action", ""), body.get("domain", "")
                if act == "set_domain" and dom:
                    set_domain_adapter(dom)
                elif act == "sync_skills_now":
                    subprocess.Popen(["ssh", f"{PC_USER}@{PC_IP}", "python3 ~/omni_auto_trainer/auto_lora_trainer.py --sync-now"])
                    add_log("🔄 Принудительное сканирование скилов на ПК", "SYNC")
                elif act == "force_train_lora":
                    subprocess.Popen(["ssh", f"{PC_USER}@{PC_IP}", "python3 ~/omni_auto_trainer/auto_lora_trainer.py --force-all"])
                    add_log("⚡ Тренировка ≤3B / подготовка Colab-очереди на ПК", "TRAIN")
                elif act == "train_domain" and dom:
                    subprocess.Popen(["ssh", f"{PC_USER}@{PC_IP}", f"python3 ~/omni_auto_trainer/auto_lora_trainer.py --force-domain {dom}"])
                    add_log(f"⚡ LoRA-очередь для домена [{dom}]", "TRAIN")
                elif act == "toggle_teacher":
                    cmd = "stop" if TEACHER_STATE == "ONLINE" else "start"
                    subprocess.Popen(["ssh", f"{PC_USER}@{PC_IP}", f"~/omni_auto_trainer/manage_teacher.sh {cmd}"])
                    add_log(f"🎓 Учитель MoE: {cmd}", "TEACHER")
                elif act == "add_folder":
                    db_exec("INSERT OR IGNORE INTO watched_folders VALUES (?,'Custom Folder','Ожидание')", (body["path"],))
                    add_log(f"📂 Папка скилов: {body['path']}")
                elif act == "vote_skill":
                    db_exec("UPDATE skills_meta SET utility_score=utility_score+? WHERE id=?", (body["delta"], body["id"]))
                elif act == "prune_skills":
                    db_exec("DELETE FROM skills_meta WHERE utility_score<=0 AND usage_count>=4")
                    add_log("🧹 База очищена от неэффективных правил")
                elif act == "poweroff_all":
                    add_log("🛑 Бэкап и выключение кластера", "SYSTEM", "alarm")
                    db_exec("PRAGMA wal_checkpoint(TRUNCATE)")
                    subprocess.run(["rsync", "-az", BASE_DIR+"/", f"{PC_USER}@{PC_IP}:~/omni_auto_trainer/backups/"], timeout=20)
                    for k in ["mi10t", "nord10"]:
                        subprocess.Popen(["ssh", "-p", "8022", NODES[k]["ip"], "su -c 'reboot -p' || poweroff"])
                    subprocess.Popen("sleep 2 && (su -c 'reboot -p' || poweroff)", shell=True)
                return self._send({"status": "ok", "action": act})

            # --- Push-телеметрия узлов ---
            if self.path == "/api/telemetry":
                node = body.get("node")
                if node in NODES:
                    TELEMETRY[node] = {**body, "online": True, "ts": time.time()}
                    if body.get("temp_c", 0) >= 46.5:
                        add_log(f"🔥 ПЕРЕГРЕВ {NODES[node]['name']}: {body['temp_c']}°C", "ALARM", "alarm")
                return self._send({"status": "ok"})

            # --- Эскалация (вызывается ПК-хуком verify_and_learn) ---
            if self.path == "/v1/escalate":
                dom = body.get("domain") or dynamic_detect_domain(body.get("prompt", ""))
                fixed, src = escalate(dom, body.get("prompt", ""), body.get("reply", ""), body.get("error", ""))
                saved = save_training_pair(dom, body.get("prompt", ""), fixed, source=f"distill_{src}")
                return self._send({"fixed": fixed, "source": src, "saved_to_lora": saved, "domain": dom})

            # --- Синхронизация скилов ---
            if self.path == "/v1/sync_skill":
                topic = body.get("topic", "Skill").strip(); content = body.get("content", "").strip()
                dom = body.get("domain") or dynamic_detect_domain(topic+" "+content)
                if dom not in ALLOWED_DOMAINS: dom = "general"
                vec = get_embedding(topic+": "+content[:1000])
                merged = topic
                if vec:
                    for rt, rv in db_query("SELECT topic,vec_json FROM skills_meta WHERE domain=? AND vec_json IS NOT NULL", (dom,)):
                        try:
                            if cosine_sim(vec, json.loads(rv)) > 0.88: merged = rt; break
                        except Exception: pass
                now_s = datetime.now().strftime("%Y-%m-%d %H:%M")
                db_exec("""INSERT INTO skills_meta(domain,topic,content,source_folder,utility_score,vec_json,updated_at)
                           VALUES (?,?,?,?,3,?,?) ON CONFLICT(topic) DO UPDATE SET
                           content=excluded.content, vec_json=excluded.vec_json, updated_at=excluded.updated_at""",
                        (dom, merged, content, body.get("source_folder", "PC_Sync"), json.dumps(vec) if vec else None, now_s))
                db_exec("DELETE FROM kb_fts WHERE topic=?", (merged,))
                db_exec("INSERT INTO kb_fts(domain,topic,content) VALUES (?,?,?)", (dom, merged, content))
                if body.get("raw_folder"):
                    db_exec("UPDATE watched_folders SET last_sync=? WHERE path=?", (datetime.now().strftime("%H:%M:%S"), body["raw_folder"]))
                save_training_pair(dom, f"Примени инженерный навык и стандарт [{merged}] в работе.", content, source="skill_sync")
                return self._send({"status": "synced", "domain": dom, "topic": merged})

            # --- Ручное / хук-обучение ---
            if self.path == "/v1/learn":
                prompt, reply = body.get("prompt", ""), body.get("response", "")
                dom = body.get("domain") or dynamic_detect_domain(prompt+" "+reply)
                if body.get("fact_summary"):
                    top = f"Learned_{int(time.time())}"
                    db_exec("INSERT OR REPLACE INTO skills_meta(domain,topic,content,source_folder,utility_score,updated_at) VALUES (?,?,?,'Direct_Learn',5,?)",
                            (dom, top, body["fact_summary"][:2000], datetime.now().strftime("%Y-%m-%d %H:%M")))
                    db_exec("INSERT INTO kb_fts(domain,topic,content) VALUES (?,?,?)", (dom, top, body["fact_summary"][:2000]))
                saved = save_training_pair(dom, prompt, reply, source="direct_learn")
                return self._send({"status": "learned", "saved_to_lora": saved, "domain": dom})

            # --- Дедуп статей ---
            if self.path == "/v1/check_duplicate":
                vec = get_embedding(f"{body.get('title','')}. {body.get('summary','')}")
                if not vec: return self._send({"is_duplicate": False, "max_similarity": 0.0})
                best, slug = 0.0, None
                for s, t, vj in db_query("SELECT slug,title,vec_json FROM articles_vec"):
                    sim = cosine_sim(vec, json.loads(vj))
                    if sim > best: best, slug = sim, s
                dup = best >= 0.85
                if not dup and body.get("save_if_unique", True) and body.get("slug"):
                    db_exec("INSERT OR REPLACE INTO articles_vec VALUES (?,?,?,?)",
                            (body["slug"], body.get("title", ""), json.dumps(vec), datetime.now().isoformat()))
                return self._send({"is_duplicate": dup, "max_similarity": round(best, 4), "matched_slug": slug})

            # --- Эмбеддинги ---
            if self.path.startswith("/v1/embeddings"):
                return self._send(http_json(EMBED_URL, body, timeout=15))

            # --- count_tokens (Claude Code) ---
            if self.path.startswith("/v1/messages/count_tokens"):
                msgs, sys_txt, _, _ = anthropic_to_oai(body)
                est = len(sys_txt)//4 + sum(len(json.dumps(m, ensure_ascii=False))//4 for m in msgs)
                return self._send({"input_tokens": max(1, est)})

            # --- ЕДИНЫЙ ЧАТ: OpenAI / Ollama / Anthropic ---
            if self.path.startswith(("/v1/chat/completions", "/api/chat", "/v1/messages")):
                return self.handle_chat(body)

            return self._send({"error": "not found"}, 404)
        except Exception as e:
            try: self._send({"error": str(e)}, 502)
            except Exception: pass

    # ---------------- маршрутизация + стриминг ----------------
    def handle_chat(self, body):
        is_anthropic = self.path.startswith("/v1/messages")
        is_ollama = self.path.startswith("/api/chat")
        req_model = body.get("model", "omni-auto").lower()
        want_stream = bool(body.get("stream", False)) or is_anthropic   # Claude Code стримит всегда

        if is_anthropic:
            msgs, sys_txt, tools, tool_choice = anthropic_to_oai(body)
        else:
            msgs = oai_clean_messages(body.get("messages", []))
            sys_txt = ""
            tools = body.get("tools"); tool_choice = body.get("tool_choice")
            # вынести system в отдельную константу-склейку
            sys_msgs = [m["content"] for m in msgs if m.get("role") == "system" and isinstance(m.get("content"), str)]
            msgs = [m for m in msgs if m.get("role") != "system"]
            sys_txt = "\n\n".join(sys_msgs)

        last_text, has_image = last_user_and_image(msgs)
        domain = dynamic_detect_domain(last_text)
        skills = fetch_active_skills(domain, last_text)

        # Маршрут
        mi = TELEMETRY.get("mi10t", {})
        mi_online = mi.get("online", True) and (time.time() - mi.get("ts", 0) < 60)
        mi_hot = mi.get("temp_c", 0) >= 47.0
        if "deep" in req_model or "flash" in req_model:
            kind = "cloud" if domain in CLOUD_DOMAINS and DEEPSEEK_KEY else "teacher"
        elif "teacher" in req_model:
            kind = "teacher"
        elif has_image:
            kind = "vision"
        elif "fast" in req_model or "haiku" in req_model or not mi_online or mi_hot:
            kind = "fast"
        else:
            kind = "brain"
        if kind == "brain":
            if globals().get("_last_kind") == "vision":
                globals()["_cur_domain"] = None   # мозг перезагружался — переустановить адаптер
            set_domain_adapter(domain)   # мгновенно, между задачами
        globals()["_last_kind"] = kind

        target = {"brain": BRAIN_URL, "vision": BRAIN_URL, "fast": FAST_URL,
                  "teacher": TEACHER_URL, "cloud": DEEPSEEK_URL}[kind]

        # Стабильный system + RAG в ХВОСТЕ (не ломаем префиксный кэш)
        final_msgs = [{"role": "system", "content": (sys_txt + "\n\n" + BASE_SYSTEM).strip()}] + msgs
        if skills:
            final_msgs.append({"role": "user", "content": f"[Контекст базы знаний, домен {domain}]:\n{skills}\nПримени эти стандарты к последнему вопросу."})

        payload = {"messages": final_msgs, "max_tokens": body.get("max_tokens", 4096),
                   "temperature": body.get("temperature", 0.7), "top_p": body.get("top_p", 0.8),
                   "stream": want_stream}
        if kind == "cloud":
            payload["model"] = DEEPSEEK_MODEL; payload["temperature"] = 0.3; payload["reasoning_effort"] = 60
        else:
            payload["chat_template_kwargs"] = {"enable_thinking": False}
            payload["model"] = {"brain": BRAIN_MODEL, "vision": VISION_MODEL}.get(kind, "triad")
        if tools:
            payload["tools"] = tools; payload["tool_choice"] = tool_choice or "auto"
        if want_stream:
            payload["stream_options"] = {"include_usage": True}

        # --- STREAM ---
        if want_stream:
            mode = "anthropic" if is_anthropic else ("ollama" if is_ollama else "openai")
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson" if is_ollama else "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "close")
            self.end_headers()
            try: self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            except Exception: pass
            relay = StreamRelay(self, mode)
            reply, usage = relay.run(target, payload)
            log_tokens(domain, usage, last_text, reply)
            return

        # --- NON-STREAM ---
        try:
            res = http_json(target, payload, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"} if kind == "cloud" else None,
                            timeout=600 if kind in ("teacher", "cloud") else 300)
        except urllib.error.HTTPError as e:
            if kind == "cloud" and e.code == 400:
                payload.pop("reasoning_effort", None)
                res = http_json(target, payload, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=180)
            else:
                raise
        choice = res["choices"][0]["message"]
        reply = choice.get("content") or ""
        usage = res.get("usage", {})
        log_tokens(domain, usage, last_text, reply)

        if is_anthropic:
            content = []
            if reply: content.append({"type": "text", "text": reply})
            for tc in choice.get("tool_calls") or []:
                fn = tc.get("function") or {}
                try: inp = json.loads(fn.get("arguments") or "{}")
                except Exception: inp = {}
                content.append({"type": "tool_use", "id": tc.get("id"), "name": fn.get("name"), "input": inp})
            stop = "tool_use" if choice.get("tool_calls") else ("max_tokens" if res["choices"][0].get("finish_reason") == "length" else "end_turn")
            return self._send({"id": f"msg_{int(time.time()*1000)}", "type": "message", "role": "assistant",
                               "model": req_model, "content": content, "stop_reason": stop, "stop_sequence": None,
                               "usage": {"input_tokens": usage.get("prompt_tokens", max(1, len(last_text)//4)),
                                         "output_tokens": usage.get("completion_tokens", max(1, len(reply)//4))}})
        if is_ollama:
            return self._send({"model": req_model, "message": {"role": "assistant", "content": reply}, "done": True,
                               "eval_count": usage.get("completion_tokens", 0)})
        return self._send(res)

# ============================ MAIN ============================
if __name__ == "__main__":
    if OMNI_TOKEN == "sk-triad":
        print("⚠️  OMNI_TOKEN по умолчанию! Задайте свой: OMNI_TOKEN=... python3 omni_gateway.py")
    threading.Thread(target=stats_flusher, daemon=True).start()
    threading.Thread(target=local_telemetry_loop, daemon=True).start()
    threading.Thread(target=teacher_watch_loop, daemon=True).start()
    threading.Thread(target=start_mdns, daemon=True).start()
    add_log("🚀 Triad-Omni Gateway v4.7 запущен", "SYSTEM")
    srv = ThreadingHTTPServer(("0.0.0.0", 8000), OmniGatewayHandler)
    srv.daemon_threads = True
    print("🚀 Triad-Omni Gateway v4.7 → http://0.0.0.0:8000")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        db_exec("PRAGMA wal_checkpoint(TRUNCATE)")
        srv.server_close()
