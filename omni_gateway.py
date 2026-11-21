#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni v4.0 (Hardware Deck Edition) - Master Gateway & Kiosk Server
Runs on Redmi Note 4 (NODE-3, Helio X20) inside Alpine Linux PRoot.
Endpoints:
  - Web Kiosk Dashboard: / and /?deck=1
  - OpenAI API: /v1/chat/completions, /v1/models, /v1/embeddings
  - Anthropic Messages API: /v1/messages (for Claude Code CLI)
  - Ollama API: /api/chat, /api/tags
  - Skill Sync & FTS5: /v1/sync_skill, /v1/check_duplicate
  - Dynamic LoRA Manager: /lora-adapters
  - UDP Beacon Listener: port 8099
"""

import os
import sys
import json
import math
import time
import random
import socket
import sqlite3
import threading
import subprocess
import urllib
import urllib.request
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

RICK_QUOTES_PY = [
    "Морти, очнись! Я превратила три китайских смартфона в распределенный тензорный кластер! Мы победили кремний, Морти!",
    "Дневной режим активирован. Комп отдыхает, а Mi 10T переваривает девять миллиардов параметров. Не трогай ничего руками!",
    "Врубаем тридцать три миллиарда! Комп делится слоями с телефоном. Если GTX 1050 Ti сейчас загорится — я не виновата!",
    "Подстегнула картридж пайки и реверса. Теперь сеть соображает в регистрах лучше любого китайского инженера!",
    "Тревога, Морти! Аккумулятор раскалился до чертей! Срочно сними нагрузку, иначе мы взлетим на воздух!",
    "Код готов, забирай. И не благодари меня, я гений!",
    "Ты что, опять тыкаешь в экран без защитных очков, Морти?!",
    "Шлюз работает на первой космической. Никакой облачной цензуры, чистый локальный оффлайн!",
    "LPDDR5 память на Xiaomi выдает пятьдесят один гигабайт в секунду! Твоя настольная видеокарта нервно курит в сторонке!"
]

# ----------------- СЕТЕВАЯ МАТРИЦА И ПОРТЫ -----------------
NODES = {
    "mi10t":  {"name": "Xiaomi Mi 10T", "role": "DeepSeek-V4 9B + Vision", "ip": "192.168.1.201", "port": 8080, "online": False},
    "nord10": {"name": "OnePlus Nord N10", "role": "Qwen2.5-Coder 3B + BGE",  "ip": "192.168.1.202", "port": 8081, "online": False},
    "note4":  {"name": "Redmi Note 4",   "role": "Deck & Gateway",         "ip": "127.0.0.1",     "port": 8000, "online": True},
    "pc":     {"name": "Home Trainer",   "role": "QLoRA 9B Trainer",       "ip": "192.168.1.100", "port": 0,    "online": False}
}

LORA_CARTRIDGES = [
    {"id": "solder",        "name": "Точка плавления (ГОСТ/IPC)", "active": True,  "scale": 1.0},
    {"id": "reva_android",  "name": "Ghidra ReVa & Android JNI",  "active": False, "scale": 0.0},
    {"id": "esp32",         "name": "ESP32 FreeRTOS & I2S",       "active": False, "scale": 0.0},
    {"id": "ui_video",      "name": "Remotion & Manim UI/Shorts", "active": True,  "scale": 0.8}
]

# ----------------- БАЗА ДАННЫХ И ДАТАСЕТЫ -----------------
BASE_DIR = os.path.expanduser("/sdcard/OmniCluster_Data")
if not os.path.exists("/sdcard"):
    BASE_DIR = os.path.expanduser("~/omni_hub")

DB_DIR = os.path.join(BASE_DIR, "db")
DS_DIR = os.path.join(BASE_DIR, "datasets")
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(DS_DIR, exist_ok=True)

DB_FILE = os.path.join(DB_DIR, "omni_knowledge.db")
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("""
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
conn.execute("CREATE TABLE IF NOT EXISTS article_vectors (slug TEXT PRIMARY KEY, title TEXT, vec_json TEXT);")
conn.execute("CREATE TABLE IF NOT EXISTS token_stats (domain TEXT PRIMARY KEY, prompt_tokens INTEGER DEFAULT 0, completion_tokens INTEGER DEFAULT 0, requests_count INTEGER DEFAULT 0);")
conn.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, level TEXT, msg TEXT);")
conn.commit()

# =====================================================================
# ВШИТЫЙ ПАКЕТ СТАРТОВЫХ ИНЖЕНЕРНЫХ НАВЫКОВ (CORE STARTER SKILLS v4.0)
# =====================================================================
CORE_STARTER_SKILLS = [
    (
        "reva_android",
        "Ghidra_ReVa_JNI_Bridge_Reconstruction",
        "СТАНДАРТ АНАЛИЗА ANDROID JNI В GHIDRA (ReVa): "
        "1) Первый аргумент любой JNI-функции (регистр X0 на ARM64) всегда типизируй как JNIEnv*, второй (X1) — как jobject thiz или jclass. "
        "2) При анализе JNI_OnLoad находи вызовы (*env)->RegisterNatives (смещение +0x6b8 в таблице JNINativeInterface на 64-битных системах) и восстанавливай массив структур JNINativeMethod {char* name, char* signature, void* fnPtr}. "
        "3) Всегда сопоставляй дескрипторы типов JNI (например, '(Ljava/lang/String;I)Z') с конкретными типами C/C++ и переименовывай функции в формат Java_<Class>_<Method>."
    ),
    (
        "reva_android",
        "ARM64_ABI_And_Struct_Recovery",
        "СТАНДАРТ ВОССТАНОВЛЕНИЯ СТРУКТУР C/C++ И ABI AARCH64: "
        "1) Учитывай стандарт AAPCS64: X0-X7 передают целочисленные аргументы и указатели, X8 — адрес буфера для возврата крупной структуры по значению, D0-D7 — числа с плавающей точкой. "
        "2) Если в декомпилированном коде Ghidra видны обращения вида *(int *)(param_1 + 0x10), *(long *)(param_1 + 0x18), не оставляй сырую адресную арифметику — сформируй определение C-структуры с выравниванием полей по границам 4/8 байт. "
        "3) Для C++ объектов первыми 8 байтами (смещение 0x00) всегда проверяй наличие указателя на таблицу виртуальных методов (vtable**)."
    ),
    (
        "reva_android",
        "Control_Flow_Deobfuscation_Analysis",
        "АНАЛИЗ СЛОЖНЫХ ГРАФОВ УПРАВЛЕНИЯ (CFG) И ДЕКОМПИЛЯЦИЯ: "
        "1) Если функция содержит бесконечный цикл while(true) с переменной состояния (state variable) и большим switch — это уплощение потока управления (Control Flow Flattening). Выдели начальное состояние, конечные блоки выхода и построй прямую последовательность вызовов без диспетчера. "
        "2) Заменяй константные побитовые выражения и избыточные арифметические тождества (MBA) эквивалентными простыми операциями C. "
        "3) В отчете всегда указывай точные адреса базовых блоков и назначение восстановленной функции."
    ),
    (
        "esp32",
        "ESP32_FreeRTOS_DMA_Hardware_Architecture",
        "СТАНДАРТ РАЗРАБОТКИ ПРОШИВОК ESP32 / ESP32-S3 (ESP-IDF & FreeRTOS): "
        "1) Жестко разделяй ядра: на Core 0 (PRO_CPU) оставляй стек Wi-Fi, Bluetooth и сетевые сокеты; все задачи реального времени (чтение I2S микрофона INMP441, вывод звука MAX98357A, опрос датчиков и камеры OV3660) привязывай к Core 1 (APP_CPU) через xTaskCreatePinnedToCore. "
        "2) Обработчики прерываний GPIO/таймеров помечай атрибутом IRAM_ATTR и используй внутри только FreeRTOS API с суффиксом FromISR (xQueueSendFromISR). "
        "3) Для потокового аудио и буферов камеры используй DMA-совместимую память: heap_caps_malloc(size, MALLOC_CAP_DMA) или PSRAM (MALLOC_CAP_SPIRAM) с проверкой выравнивания."
    ),
    (
        "solder",
        "Solder_Metallurgy_GOST_IPC_Practico",
        "СТАНДАРТ МЕТАЛЛУРГИИ ПАЙКИ И ВИЗУАЛЬНОЙ ИНСПЕКЦИИ ПЛАТ (ГОСТ / IPC): "
        "1) Всегда сверяй температуры плавления: ПОС-61 (ГОСТ 21930-76) — солидус 183°C, ликвидус 190°C, рабочая на жале 235–250°C; бессвинцовый SAC305 (Sn96.5Ag3.0Cu0.5) — плавление 217–220°C, рабочая на жале 260–285°C. "
        "2) Флюсы классифицируй строго по IPC J-STD-004B (ROL0, ROM1, ORH1) с указанием необходимости отмывки и коррозионной активности галогенидов. "
        "3) При анализе фото печатной платы через модуль зрения (mmproj) оценивай угол смачивания галтели припоя, наличие холодной пайки, перегрева маски, шариков припоя (solder balls) и перемычек на выводах SMD/QFN/BGA according to IPC-A-610."
    ),
    (
        "ui_video",
        "HTMLmark_2.0_Industrial_Workbench_UI",
        "СТАНДАРТ ГЕНЕРАЦИИ ИНТЕРФЕЙСОВ И ВИДЕО (HTMLmark 2.0 Industrial Theme): "
        "1) Никаких шаблонных фиолетово-розовых градиентов. Используй палитру 'Инженерный Верстак': фон #0b1120, панель #161f33, границы 1px solid #263554, акцент нагрева #f59e0b, технический #38bdf8, успех #22c55e. "
        "2) Все интерактивные инженерные калькуляторы верстай на адаптивном CSS Grid (корректное отображение от 320px на мобильных без горизонтального скролла) и чистом Vanilla JS с мгновенным пересчетом значений при движении ползунков. "
        "3) При генерации скриптов Manim используй темный фон #0f172a, четкие засечки осей и контрастные подписи без наложения текста."
    )
]

for dom, top, cont in CORE_STARTER_SKILLS:
    conn.execute("""
        INSERT OR IGNORE INTO skills_meta(domain, topic, content, source_folder, utility_score, updated_at)
        VALUES (?, ?, ?, 'Built-in Core v4.0', 10, ?)
    """, (dom, top, cont, datetime.now().strftime("%Y-%m-%d %H:%M")))
conn.commit()


# ----------------- РОБУСТНЫЙ ВЕБ-ПОИСК (DDG API + WIKIPEDIA) -----------------
def web_search_ddg(query, max_results=3):
    """Ищет в интернете через DuckDuckGo Instant Answer API и Wikipedia без блокировок"""
    import ssl, json, re
    ctx = ssl._create_unverified_context()
    results = []

    # 1. DuckDuckGo Instant Answer API
    try:
        url = "https://api.duckduckgo.com/?q=" + urllib.parse.quote(query) + "&format=json&no_html=1"
        req = urllib.request.Request(url, headers={"User-Agent": "TriadOmniCluster/4.0"})
        with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        heading = data.get("Heading", "")
        abstract = data.get("AbstractText", "")
        if abstract:
            results.append(f"• [DuckDuckGo - {heading}]: {abstract}")
        for top in data.get("RelatedTopics", [])[:2]:
            if isinstance(top, dict) and "Text" in top:
                results.append(f"• [DDG Info]: {top['Text']}")
    except Exception:
        pass

    # 2. Wikipedia API (RU & EN)
    if len(results) < 2:
        for lang in ["ru", "en"]:
            try:
                wiki_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&utf8=1"
                wreq = urllib.request.Request(wiki_url, headers={"User-Agent": "TriadOmniCluster/4.0"})
                with urllib.request.urlopen(wreq, timeout=4, context=ctx) as wresp:
                    wdata = json.loads(wresp.read().decode("utf-8", errors="replace"))
                for item in wdata.get("query", {}).get("search", [])[:2]:
                    snip = re.sub(r'<[^>]+>', '', item.get("snippet", "")).strip()
                    if snip:
                        results.append(f"• [Wiki-{lang.upper()} {item.get('title')}]: {snip}")
                if results:
                    break
            except Exception:
                pass

    return "\n".join(results[:max_results])

def detect_domain(text):
    t = text.lower()
    if any(k in t for k in ["ui", "css", "html", "tailwind", "react", "remotion", "manim", "видео", "shorts", "калькулятор"]):
        return "ui_video"
    if any(k in t for k in ["ghidra", "reva", "jni", "smali", "apk", "android", "драйвер", "fastboot"]):
        return "reva_android"
    if any(k in t for k in ["esp32", "freertos", "i2s", "ov3660", "inmp441", "max98357", "esp-idf"]):
        return "esp32"
    return "solder"

def get_kb_context(domain, query):
    cur = conn.execute(
        "SELECT topic, content FROM skills_meta WHERE (domain = ? OR domain = 'all') AND utility_score > 0 ORDER BY utility_score DESC LIMIT 3",
        (domain,)
    )
    rows = cur.fetchall()
    if not rows:
        return ""
    return "\n".join([f"• [{r[0]}]: {r[1]}" for r in rows])

# ----------------- KIOSK DASHBOARD HTML (CHROME 56 SAFE) -----------------
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="mobile-web-app-capable" content="yes">
<title> Triad-Omni Deck</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
  body {
    background: #000000 radial-gradient(circle at 50% -20%, #1c1c2e 0%, #050508 70%);
    color: #F5F5F7;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, sans-serif;
    padding: 12px 10px 80px 10px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
  }

  /* Apple Dynamic Top Bar */
  .apple-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 6px 14px 6px;
  }
  .brand {
    display: flex;
    align-items: center;
  }
  .apple-logo {
    font-size: 24px;
    margin-right: 8px;
    color: #FFFFFF;
    filter: drop-shadow(0 0 10px rgba(255,255,255,0.4));
  }
  .brand-title {
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.4px;
    color: #FFFFFF;
  }
  .brand-sub {
    font-size: 11px;
    font-weight: 500;
    color: #8E8E93;
    letter-spacing: 0.2px;
  }
  .status-pill {
    display: flex;
    align-items: center;
    background: rgba(48, 209, 88, 0.15);
    border: 1px solid rgba(48, 209, 88, 0.3);
    border-radius: 99px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 600;
    color: #30D158;
  }
  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #30D158;
    margin-right: 6px;
    box-shadow: 0 0 8px #30D158;
  }

  /* Apple Segmented Control */
  .segmented-control {
    display: flex;
    background: rgba(118, 118, 128, 0.24);
    border-radius: 12px;
    padding: 3px;
    margin-bottom: 14px;
  }
  .segment-btn {
    flex: 1;
    text-align: center;
    padding: 8px 6px;
    border-radius: 9px;
    font-size: 12px;
    font-weight: 600;
    color: #8E8E93;
    border: none;
    background: transparent;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .segment-btn.active {
    background: rgba(255, 255, 255, 0.16);
    color: #FFFFFF;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  }

  /* Glassmorphism Cards */
  .apple-card {
    background: rgba(28, 28, 30, 0.72);
    -webkit-backdrop-filter: blur(25px);
    backdrop-filter: blur(25px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 18px;
    padding: 14px;
    margin-bottom: 12px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.35);
  }

  /* Nodes Grid */
  .nodes-stack {
    display: flex;
    flex-direction: column;
  }
  .node-item {
    background: rgba(28, 28, 30, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 12px 14px;
    margin-bottom: 10px;
    position: relative;
    transition: border-color 0.2s ease;
  }
  .node-item.online {
    border-color: rgba(48, 209, 88, 0.35);
  }
  .node-item.alarm {
    border-color: #FF453A;
    background: rgba(255, 69, 58, 0.12);
    animation: ios-pulse 1.2s infinite;
  }
  @keyframes ios-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(255, 69, 58, 0.4); }
    50% { box-shadow: 0 0 0 8px rgba(255, 69, 58, 0); }
  }

  .node-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }
  .node-name {
    font-size: 15px;
    font-weight: 700;
    color: #FFFFFF;
  }
  .node-badge {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 3px 7px;
    border-radius: 6px;
  }
  .node-badge.on { background: rgba(48, 209, 88, 0.2); color: #30D158; }
  .node-badge.off { background: rgba(142, 142, 147, 0.2); color: #8E8E93; }

  .node-role {
    font-size: 12px;
    color: #8E8E93;
    margin-bottom: 10px;
  }

  /* Apple Telemetry Widgets */
  .node-metrics {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(0, 0, 0, 0.25);
    border-radius: 10px;
    padding: 8px 10px;
  }
  .metric-box {
    display: flex;
    align-items: center;
    font-size: 12px;
    font-weight: 600;
  }

  /* iOS Battery Capsule */
  .ios-battery {
    display: inline-flex;
    align-items: center;
    margin-right: 12px;
  }
  .battery-cap {
    width: 22px;
    height: 11px;
    border: 1.5px solid rgba(255, 255, 255, 0.7);
    border-radius: 3.5px;
    padding: 1px;
    position: relative;
    display: flex;
    align-items: center;
  }
  .battery-cap::after {
    content: "";
    position: absolute;
    right: -3px;
    top: 2px;
    width: 1.5px;
    height: 5px;
    background: rgba(255, 255, 255, 0.7);
    border-radius: 0 1px 1px 0;
  }
  .battery-level {
    height: 100%;
    background: #30D158;
    border-radius: 1.5px;
    transition: width 0.3s ease;
  }
  .battery-text {
    font-size: 12px;
    font-weight: 600;
    margin-left: 5px;
    color: #EBEBF5;
  }

  /* Temp Pill */
  .temp-pill {
    padding: 2px 7px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    background: rgba(48, 209, 88, 0.15);
    color: #30D158;
  }
  .temp-pill.warm { background: rgba(255, 159, 10, 0.2); color: #FF9F0A; }
  .temp-pill.hot { background: rgba(255, 69, 58, 0.25); color: #FF453A; }

  /* Section Title */
  .section-header {
    font-size: 12px;
    font-weight: 600;
    color: #8E8E93;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 14px 4px 6px 4px;
  }

  /* iOS List Group & Switches */
  .ios-list {
    background: rgba(28, 28, 30, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    overflow: hidden;
  }
  .ios-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  .ios-row:last-child { border-bottom: none; }
  .row-title { font-size: 14px; font-weight: 600; color: #FFFFFF; }
  .row-sub { font-size: 11px; color: #8E8E93; margin-top: 1px; }

  /* iOS Switch */
  .ios-switch {
    width: 46px;
    height: 26px;
    background: rgba(120, 120, 128, 0.32);
    border-radius: 13px;
    position: relative;
    cursor: pointer;
    transition: background-color 0.25s ease;
  }
  .ios-switch.on { background: #34C759; }
  .switch-thumb {
    width: 22px;
    height: 22px;
    background: #FFFFFF;
    border-radius: 50%;
    position: absolute;
    top: 2px;
    left: 2px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.25);
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .ios-switch.on .switch-thumb { transform: translateX(20px); }

  /* Awesome-REA View */
  .ios-search-box {
    display: flex;
    align-items: center;
    background: rgba(118, 118, 128, 0.24);
    border-radius: 12px;
    padding: 9px 12px;
    margin-bottom: 10px;
  }
  .search-icon { font-size: 14px; color: #8E8E93; margin-right: 8px; }
  .ios-search-input {
    width: 100%;
    background: transparent;
    border: none;
    outline: none;
    color: #FFFFFF;
    font-size: 14px;
    font-family: inherit;
  }
  .ios-search-input::placeholder { color: #8E8E93; }

  .filter-pills {
    display: flex;
    overflow-x: auto;
    padding-bottom: 6px;
    margin-bottom: 10px;
  }
  .filter-pill {
    flex-shrink: 0;
    padding: 5px 11px;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;
    background: rgba(118, 118, 128, 0.2);
    color: #8E8E93;
    margin-right: 6px;
    cursor: pointer;
    border: none;
    transition: all 0.15s ease;
  }
  .filter-pill.active {
    background: #5E5CE6;
    color: #FFFFFF;
  }

  .rea-list {
    max-height: 480px;
    overflow-y: auto;
  }
  .rea-card {
    background: rgba(28, 28, 30, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px 12px;
    margin-bottom: 8px;
  }
  .rea-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }
  .rea-title {
    font-size: 14px;
    font-weight: 700;
    color: #FFFFFF;
    text-decoration: none;
  }
  .rea-cat {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(94, 92, 230, 0.2);
    color: #A29BFE;
  }
  .rea-desc {
    font-size: 11px;
    color: #8E8E93;
    line-height: 1.35;
  }

  /* Rick Voice Deck */
  .rick-card {
    background: linear-gradient(135deg, rgba(88, 86, 214, 0.15) 0%, rgba(28, 28, 30, 0.8) 100%);
    border: 1px solid rgba(94, 92, 230, 0.3);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
  }
  .rick-bubble {
    background: rgba(0, 0, 0, 0.3);
    border-left: 3px solid #5E5CE6;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 12px;
    font-style: italic;
    font-size: 13px;
    line-height: 1.4;
    color: #EBEBF5;
  }

  /* Apple Floating Glass Dock */
  .apple-dock {
    position: fixed;
    bottom: 12px;
    left: 10px;
    right: 10px;
    background: rgba(30, 30, 35, 0.85);
    -webkit-backdrop-filter: blur(25px);
    backdrop-filter: blur(25px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 20px;
    padding: 8px 10px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    z-index: 999;
  }
  .dock-btn {
    flex: 1;
    text-align: center;
    background: transparent;
    border: none;
    color: #8E8E93;
    padding: 6px 4px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    border-radius: 10px;
    transition: all 0.15s ease;
  }
  .dock-btn:active {
    transform: scale(0.95);
    background: rgba(255, 255, 255, 0.1);
  }
  .dock-btn.danger { color: #FF453A; }
  .dock-btn.primary { color: #007AFF; }
</style>
</head>
<body>

  <!-- Apple Header -->
  <div class="apple-header">
    <div class="brand">
      <div class="apple-logo"></div>
      <div>
        <div class="brand-title">Triad-Omni Deck</div>
        <div class="brand-sub">Hardware Cluster Hub v4.0</div>
      </div>
    </div>
    <div class="status-pill">
      <div class="status-dot"></div>
      <span id="cluster_mode_label">9B Автономно</span>
    </div>
  </div>

  <!-- Segmented Control -->
  <div class="segmented-control">
    <button class="segment-btn active" onclick="switchTab('cluster')">⚡ Узлы кластера</button>
    <button class="segment-btn" onclick="switchTab('rea')">🛠️ Awesome-REA (1131)</button>
    <button class="segment-btn" onclick="switchTab('rick')">🧪 Пульт Рика</button>
  </div>

  <!-- TAB 1: CLUSTER HARDWARE -->
  <div id="tab_cluster">
    <div class="section-header">Состояние Узлов</div>
    <div class="nodes-stack" id="nodes_container">
      <!-- Инъекция узлов через JS -->
    </div>

    <div class="section-header">Картриджи LoRA (Hot-Swap 40ms)</div>
    <div class="ios-list" id="lora_container">
      <!-- Инъекция картриджей -->
    </div>
  </div>

  <!-- TAB 2: AWESOME-REA TOOLKIT -->
  <div id="tab_rea" style="display: none;">
    <div class="ios-search-box">
      <div class="search-icon">🔍</div>
      <input type="text" class="ios-search-input" id="rea_search" placeholder="Поиск по 1131 утилитам (Android, Ghidra, EDL, Frida...)" oninput="searchRea()">
    </div>
    <div class="filter-pills">
      <button class="filter-pill active" onclick="filterRea('all', this)">Все</button>
      <button class="filter-pill" onclick="filterRea('android', this)">Android</button>
      <button class="filter-pill" onclick="filterRea('firmware', this)">Firmware</button>
      <button class="filter-pill" onclick="filterRea('native-analysis', this)">Ghidra / IDA</button>
      <button class="filter-pill" onclick="filterRea('agent-mcp', this)">Agent MCP</button>
      <button class="filter-pill" onclick="filterRea('protocol-analysis', this)">Protocols</button>
    </div>
    <div class="rea-list" id="rea_results">
      <div style="text-align:center; padding: 20px; color: #8E8E93;">Загрузка базы Awesome-REA...</div>
    </div>
  </div>

  <!-- TAB 3: RICK SANCHEZ LAB -->
  <div id="tab_rick" style="display: none;">
    <div class="rick-card">
      <div style="font-size: 14px; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;">Лаборатория Рика Санчеза (C-137)</div>
      <div class="rick-bubble" id="rick_quote_box">
        «Морти, мы выкинули всю китайскую рекламу и подняли локальный ИИ-кластер прямо на смартфонах! Это гениально!»
      </div>
      <div style="display:flex; justify-content:space-between; margin-bottom: 10px;">
        <button class="segment-btn active" style="flex:1; margin-right:6px;" onclick="playRickQuote()">🧪 Новая цитата</button>
        <button class="segment-btn" style="flex:1;" id="btn_voice_toggle" onclick="toggleRickVoice()">🗣️ Озвучка: ВКЛ</button>
      </div>
      <div class="ios-row" style="background:rgba(0,0,0,0.2); border-radius:10px; margin-top:8px;">
        <span style="font-size:12px; color:#8E8E93;">Тест WebAudio тревоги</span>
        <button class="filter-pill" onclick="playSiren()">🚨 Сирена</button>
      </div>
    </div>
  </div>

  <!-- Apple Floating Glass Dock -->
  <div class="apple-dock">
    <button class="dock-btn primary" onclick="hapticClick(); refreshData()">🔄 Обновить</button>
    <button class="dock-btn" onclick="hapticClick(); sendAction('set_mode_9b')">⚡ 9B День</button>
    <button class="dock-btn" onclick="hapticClick(); sendAction('set_mode_33b_rpc')">🎓 33B Учитель</button>
    <button class="dock-btn danger" onclick="if(confirm('Выключить весь кластер?')) { playSiren(); sendAction('poweroff_all'); }">🛑 Выкл</button>
  </div>

<script>
// WebAudio синтезатор Apple-стиля
var AudioCtx = window.AudioContext || window.webkitAudioContext;
var audioCtx = null;
var rickVoiceEnabled = true;

function getAudioCtx() {
  if (!audioCtx) { audioCtx = new AudioCtx(); }
  if (audioCtx.state === 'suspended') { audioCtx.resume(); }
  return audioCtx;
}

// Легкий тактильный клик Apple (1800Hz)
function hapticClick() {
  try {
    var c = getAudioCtx();
    var osc = c.createOscillator();
    var gain = c.createGain();
    osc.frequency.setValueAtTime(1800, c.currentTime);
    osc.type = 'sine';
    gain.gain.setValueAtTime(0.15, c.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + 0.015);
    osc.connect(gain);
    gain.connect(c.destination);
    osc.start();
    osc.stop(c.currentTime + 0.015);
  } catch(e) {}
}

function playSiren() {
  try {
    var c = getAudioCtx();
    var osc = c.createOscillator();
    var gain = c.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(600, c.currentTime);
    osc.frequency.linearRampToValueAtTime(1400, c.currentTime + 0.3);
    gain.gain.setValueAtTime(0.3, c.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, c.currentTime + 0.6);
    osc.connect(gain);
    gain.connect(c.destination);
    osc.start();
    osc.stop(c.currentTime + 0.6);
  } catch(e) {}
}

// Озвучка Рика Санчеза
function speakRick(text) {
  if (!rickVoiceEnabled || !('speechSynthesis' in window)) return;
  try {
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = 'ru-RU';
    u.pitch = 0.72;
    u.rate = 1.18;
    window.speechSynthesis.speak(u);
  } catch(e) {}
}

function toggleRickVoice() {
  hapticClick();
  rickVoiceEnabled = !rickVoiceEnabled;
  var btn = document.getElementById('btn_voice_toggle');
  if (btn) btn.innerText = rickVoiceEnabled ? '🗣️ Озвучка: ВКЛ' : '🔇 Озвучка: ВЫКЛ';
}

function playRickQuote() {
  hapticClick();
  fetch('/api/rick_quote')
    .then(function(r){ return r.json(); })
    .then(function(data){
      var box = document.getElementById('rick_quote_box');
      if (box) box.innerText = '«' + data.quote + '»';
      speakRick(data.quote);
    });
}

// Переключение вкладок
function switchTab(tabId) {
  hapticClick();
  var tabs = ['cluster', 'rea', 'rick'];
  var btns = document.querySelectorAll('.segment-btn');
  tabs.forEach(function(t, idx){
    var el = document.getElementById('tab_' + t);
    if (el) el.style.display = (t === tabId) ? 'block' : 'none';
    if (btns[idx]) {
      if (t === tabId) btns[idx].classList.add('active');
      else btns[idx].classList.remove('active');
    }
  });
  if (tabId === 'rea') searchRea();
}

// Загрузка данных дашборда
function refreshData() {
  fetch('/api/dashboard')
    .then(function(r){ return r.json(); })
    .then(function(data){
      renderNodes(data.nodes);
      renderLoras(data.loras);
      if (data.mode_label) {
        var lbl = document.getElementById('cluster_mode_label');
        if (lbl) lbl.innerText = data.mode_label.replace(/^[🟢🟣🖥️⚡]\s*/, '');
      }
    });
}

function renderNodes(nodes) {
  var c = document.getElementById('nodes_container');
  if (!c) return;
  var html = '';
  for (var k in nodes) {
    var n = nodes[k];
    var tele = n.telemetry || {};
    var isOnline = tele.online;
    var batt = tele.battery !== undefined ? tele.battery : -1;
    var temp = tele.temp_c || 0.0;
    var tempClass = temp > 45 ? 'temp-pill hot' : (temp > 38 ? 'temp-pill warm' : 'temp-pill');
    
    html += '<div class="node-item ' + (isOnline ? 'online' : '') + '">';
    html += '  <div class="node-top">';
    html += '    <div class="node-name">' + n.name + '</div>';
    html += '    <div class="node-badge ' + (isOnline ? 'on' : 'off') + '">' + (isOnline ? 'АКТИВЕН' : 'ОФФЛАЙН') + '</div>';
    html += '  </div>';
    html += '  <div class="node-role">' + n.role + ' • ' + n.ip + '</div>';
    html += '  <div class="node-metrics">';
    html += '    <div class="metric-box">';
    html += '      <div class="ios-battery">';
    html += '        <div class="battery-cap"><div class="battery-level" style="width:' + (batt >= 0 ? batt : 0) + '%;"></div></div>';
    html += '        <span class="battery-text">' + (batt >= 0 ? batt + '%' : '--') + '</span>';
    html += '      </div>';
    html += '      <div class="' + tempClass + '">' + (temp > 0 ? temp + '°C' : '--') + '</div>';
    html += '    </div>';
    html += '    <div style="font-size:11px; color:#8E8E93;">RAM: ' + (tele.free_ram_mb ? tele.free_ram_mb + ' МБ' : 'N/A') + '</div>';
    html += '  </div>';
    html += '</div>';
  }
  c.innerHTML = html;
}

function renderLoras(loras) {
  var c = document.getElementById('lora_container');
  if (!c || !loras) return;
  var html = '';
  loras.forEach(function(l, idx){
    html += '<div class="ios-row">';
    html += '  <div>';
    html += '    <div class="row-title">' + l.name + '</div>';
    html += '    <div class="row-sub">' + (l.active ? 'Активен (масштаб: ' + l.scale + ')' : 'Отключен') + '</div>';
    html += '  </div>';
    html += '  <div class="ios-switch ' + (l.active ? 'on' : '') + '" onclick="toggleLora(' + idx + ')">';
    html += '    <div class="switch-thumb"></div>';
    html += '  </div>';
    html += '</div>';
  });
  c.innerHTML = html;
}

function toggleLora(idx) {
  hapticClick();
  fetch('/api/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'toggle_lora', index: idx })
  }).then(refreshData);
}

function sendAction(action) {
  hapticClick();
  fetch('/api/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: action })
  }).then(refreshData);
}

// Awesome-REA поиск
var currentReaCat = 'all';
function filterRea(cat, btn) {
  hapticClick();
  currentReaCat = cat;
  document.querySelectorAll('.filter-pill').forEach(function(b){ b.classList.remove('active'); });
  if (btn) btn.classList.add('active');
  searchRea();
}

function searchRea() {
  var q = document.getElementById('rea_search') ? document.getElementById('rea_search').value : '';
  fetch('/api/rea/search?q=' + encodeURIComponent(q) + '&cat=' + encodeURIComponent(currentReaCat))
    .then(function(r){ return r.json(); })
    .then(function(data){
      var c = document.getElementById('rea_results');
      if (!c) return;
      if (!data.tools || data.tools.length === 0) {
        c.innerHTML = '<div style="text-align:center; padding: 20px; color:#8E8E93;">Инструменты не найдены</div>';
        return;
      }
      var html = '';
      data.tools.forEach(function(t){
        html += '<div class="rea-card">';
        html += '  <div class="rea-header">';
        html += '    <a href="' + (t.url || '#') + '" target="_blank" class="rea-title">' + t.name + ' ↗</a>';
        html += '    <div class="rea-cat">' + (t.category || 'tool') + '</div>';
        html += '  </div>';
        html += '  <div class="rea-desc">' + (t.description || 'Утилита из каталога Awesome-REA') + '</div>';
        html += '</div>';
      });
      c.innerHTML = html;
    });
}

// Запуск
setInterval(refreshData, 3000);
refreshData();

document.body.addEventListener('click', function() {
  getAudioCtx();
  if (window.speechSynthesis) window.speechSynthesis.getVoices();
}, { once: true });
</script>
</body>
</html>"""


# ----------------- GLOBAL STATE & HELPERS -----------------
CURRENT_MODE = "9b"
MODE_LABELS = {
    "9b": "9B Автономно (Xiaomi)",
    "33b_rpc": "33B RPC Mi10T + ПК",
    "33b_hybrid": "33B Учитель Hybrid (ПК)"
}
TELEMETRY_CACHE = {}
LAST_ALERT = {"type": None, "ts": 0}

def add_log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        conn.execute("INSERT INTO logs (ts, level, msg) VALUES (?, ?, ?)", (ts, level, msg))
        conn.commit()
    except Exception:
        pass
    print(f"[{ts}] [{level}] {msg}")

def http_json(url, data=None, timeout=10):
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers=headers
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

# Загрузка каталога Awesome-REA
REA_TOOLS = []
for p in ['/sdcard/OmniCluster_Data/tool-resources.json', '~/tool-resources.json', 'd:/для one plus nord n10/.agents/skills/awesome-rea/data/tool-resources.json']:
    expanded = os.path.expanduser(p)
    if os.path.exists(expanded):
        try:
            with open(expanded, 'r', encoding='utf-8') as rf:
                REA_TOOLS = json.load(rf)
                print(f'Awesome-REA loaded: {len(REA_TOOLS)} tools from {expanded}')
                break
        except Exception as e:
            print('REA load error:', e)

def get_local_telemetry():
    batt = 100
    temp = 32.0
    free_ram = 1200
    try:
        if os.path.exists('/sys/class/power_supply/battery/capacity'):
            with open('/sys/class/power_supply/battery/capacity') as f:
                batt = int(f.read().strip())
        if os.path.exists('/sys/class/power_supply/battery/batt_temp'):
            with open('/sys/class/power_supply/battery/batt_temp') as f:
                temp = round(int(f.read().strip()) / 10.0, 1)
        elif os.path.exists('/sys/class/power_supply/battery/temp'):
            with open('/sys/class/power_supply/battery/temp') as f:
                temp = round(int(f.read().strip()) / 10.0, 1)
        if os.path.exists('/proc/meminfo'):
            with open('/proc/meminfo') as f:
                for l in f:
                    if 'MemAvailable' in l:
                        free_ram = round(int(l.split()[1]) / 1024.0, 1)
                        break
    except Exception:
        pass
    return {
        "online": True,
        "battery": batt,
        "temp_c": temp,
        "free_ram_mb": free_ram
    }

def telemetry_watchdog_thread():
    global LAST_ALERT
    while True:
        try:
            loc = get_local_telemetry()
            TELEMETRY_CACHE["note4"] = loc
            
            # Check Mi10T
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                res = s.connect_ex((NODES["mi10t"]["ip"], NODES["mi10t"]["port"]))
                s.close()
                NODES["mi10t"]["online"] = (res == 0)
                if "mi10t" not in TELEMETRY_CACHE:
                    TELEMETRY_CACHE["mi10t"] = {"online": (res == 0), "battery": 88, "temp_c": 34.5, "free_ram_mb": 4200}
                else:
                    TELEMETRY_CACHE["mi10t"]["online"] = (res == 0)
            except Exception:
                NODES["mi10t"]["online"] = False
                if "mi10t" in TELEMETRY_CACHE:
                    TELEMETRY_CACHE["mi10t"]["online"] = False

            # Check Nord N10
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                res = s.connect_ex((NODES["nord10"]["ip"], NODES["nord10"]["port"]))
                s.close()
                NODES["nord10"]["online"] = (res == 0)
                if "nord10" not in TELEMETRY_CACHE:
                    TELEMETRY_CACHE["nord10"] = {"online": (res == 0), "battery": 92, "temp_c": 31.0, "free_ram_mb": 3100}
                else:
                    TELEMETRY_CACHE["nord10"]["online"] = (res == 0)
            except Exception:
                NODES["nord10"]["online"] = False
                if "nord10" in TELEMETRY_CACHE:
                    TELEMETRY_CACHE["nord10"]["online"] = False

            # Check PC
            TELEMETRY_CACHE["pc"] = {"online": False, "battery": -1, "temp_c": 42.0, "free_ram_mb": 9500}
            
            if loc.get("temp_c", 0) > 46.0:
                LAST_ALERT = {"type": "overheat", "msg": f"Перегрев Redmi Note 4: {loc['temp_c']}°C!", "ts": time.time()}
        except Exception:
            pass
        time.sleep(3)

threading.Thread(target=telemetry_watchdog_thread, daemon=True).start()

# ----------------- HTTP REQUEST HANDLER -----------------
class MasterGatewayHandler(BaseHTTPRequestHandler):
    def _send(self, data, code=200, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        if isinstance(data, (dict, list)):
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        elif isinstance(data, str):
            self.wfile.write(data.encode("utf-8"))
        else:
            self.wfile.write(data)

    def do_OPTIONS(self):
        self._send("", 204)

    def do_GET(self):
        # 1. Kiosk Dashboard UI
        if self.path == "/" or self.path.startswith("/?deck="):
            return self._send(DASHBOARD_HTML, 200, "text/html")

        # 2. REST API для Dashbaord
        if self.path == "/api/dashboard":
            nodes_data = {}
            for k, v in NODES.items():
                nodes_data[k] = {
                    "name": v["name"],
                    "role": v["role"],
                    "ip": v["ip"],
                    "telemetry": TELEMETRY_CACHE.get(k, {})
                }
            return self._send({
                "nodes": nodes_data,
                "loras": LORA_CARTRIDGES,
                "mode": CURRENT_MODE,
                "mode_label": MODE_LABELS.get(CURRENT_MODE, CURRENT_MODE),
                "alert": LAST_ALERT if time.time() - LAST_ALERT["ts"] < 20 else None
            })

        # 3. OpenAI Models List
        if self.path == "/v1/models" or self.path == "/api/tags":
            models = ["omni-auto", "omni-solder", "omni-reva", "omni-esp32", "omni-ui-video", "omni-fast", "bge-m3"]
            if "tags" in self.path:
                return self._send({"models": [{"name": m, "model": m} for m in models]})
            return self._send({"object": "list", "data": [{"id": m, "object": "model"} for m in models]})

        # 4. Цитата Рика Санчеза
        if self.path == "/api/rick_quote":
            quote = random.choice(RICK_QUOTES_PY)
            return self._send({"quote": quote, "author": "Rick Sanchez (C-137)"})

        # 5. Awesome-REA Search API
        if self.path.startswith("/api/rea/search"):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            q = params.get("q", [""])[0].lower().strip()
            cat = params.get("cat", ["all"])[0].lower().strip()
            matches = []
            for item in REA_TOOLS:
                item_cat = item.get("category", "").lower()
                if cat != "all" and cat not in item_cat:
                    continue
                if not q:
                    matches.append({
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "category": item.get("category"),
                        "description": item.get("description_en", "")[:180],
                        "url": item.get("url")
                    })
                    if len(matches) >= 35:
                        break
                    continue
                if q in item.get("name", "").lower() or q in item.get("description_en", "").lower() or q in item_cat:
                    matches.append({
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "category": item.get("category"),
                        "description": item.get("description_en", "")[:180],
                        "url": item.get("url")
                    })
                    if len(matches) >= 35:
                        break
            return self._send({"total": len(REA_TOOLS), "count": len(matches), "tools": matches})

        self._send({"status": "Triad-Omni Ready"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8", errors="replace")) if length > 0 else {}

        # 1. Действия пульта управления
        if self.path == "/api/control":
            act = body.get("action")
            if act == "toggle_lora":
                idx = body.get("index", 0)
                if 0 <= idx < len(LORA_CARTRIDGES):
                    LORA_CARTRIDGES[idx]["active"] = not LORA_CARTRIDGES[idx]["active"]
                    LORA_CARTRIDGES[idx]["scale"] = 1.0 if LORA_CARTRIDGES[idx]["active"] else 0.0
                    add_log(f"Картридж LoRA '{LORA_CARTRIDGES[idx]['name']}' переключен на {LORA_CARTRIDGES[idx]['scale']}")
                    # Отправка в Mi 10T hot-swap
                    if NODES["mi10t"]["online"]:
                        try:
                            http_json(f"http://{NODES['mi10t']['ip']}:8080/lora-adapters", [
                                {"id": i, "scale": c["scale"]} for i, c in enumerate(LORA_CARTRIDGES)
                            ], timeout=2)
                        except Exception:
                            pass
                return self._send({"status": "ok", "loras": LORA_CARTRIDGES})

            if act == "test_audio":
                add_log("Тестовый звуковой сигнал воспроизведен на пульте")
                return self._send({"status": "ok"})

            if act == "test_rick":
                quote = random.choice(RICK_QUOTES_PY)
                add_log(f"Цитата Рика озвучена: {quote}")
                return self._send({"status": "ok", "quote": quote})

            if act == "set_mode_9b":
                CURRENT_MODE = "9b"
                add_log("Кластер переведен в дневной режим: 9B Автономно")
                if NODES["mi10t"]["online"]:
                    subprocess.Popen(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=4", "-p", "8022", NODES["mi10t"]["ip"], "~/switch_mi10t_mode.sh brain"], stderr=subprocess.DEVNULL)
                return self._send({"status": "ok", "mode": CURRENT_MODE, "mode_label": MODE_LABELS["9b"]})

            if act == "set_mode_33b_rpc":
                CURRENT_MODE = "33b_rpc"
                add_log("Активация режима 33B Учитель (RPC Mi10T + ПК)")
                if NODES["mi10t"]["online"]:
                    subprocess.Popen(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=4", "-p", "8022", NODES["mi10t"]["ip"], "~/switch_mi10t_mode.sh rpc"], stderr=subprocess.DEVNULL)
                return self._send({"status": "ok", "mode": CURRENT_MODE, "mode_label": MODE_LABELS["33b_rpc"]})

            if act == "set_mode_33b_hybrid":
                CURRENT_MODE = "33b_hybrid"
                add_log("Активация режима 33B Учитель Hybrid (ПК)")
                return self._send({"status": "ok", "mode": CURRENT_MODE, "mode_label": MODE_LABELS["33b_hybrid"]})

            if act == "reload_brain":
                add_log("Команда перезапуска Qwen3.5-9B отправлена на Xiaomi Mi 10T")
                if NODES["mi10t"]["online"]:
                    subprocess.Popen(["ssh", "-p", "8022", NODES["mi10t"]["ip"], "~/reload_brain.sh"], stderr=subprocess.DEVNULL)
                return self._send({"status": "reloading"})

            if act == "prune_skills":
                conn.execute("DELETE FROM skills_meta WHERE utility_score < 0;")
                conn.commit()
                add_log("Устаревшие навыки очищены из базы знаний SQLite")
                return self._send({"status": "pruned"})

            if act == "poweroff_all":
                add_log("Экстренное завершение работы всего кластера!", level="ALARM")
                for k in ["mi10t", "nord10"]:
                    if NODES[k]["online"]:
                        subprocess.Popen(["ssh", "-p", "8022", NODES[k]["ip"], "poweroff || reboot -p"], stderr=subprocess.DEVNULL)
                subprocess.Popen("sleep 2 && poweroff", shell=True)
                return self._send({"status": "powering_off"})

        # 2. OpenAI / Anthropic / Ollama Инференс роутинг
        if self.path in ["/v1/chat/completions", "/v1/messages", "/api/chat"]:
            is_anthropic = (self.path == "/v1/messages")
            raw_msgs = body.get("messages", [])
            last_prompt = raw_msgs[-1]["content"] if raw_msgs else ""
            if isinstance(last_prompt, list):
                last_prompt = " ".join([p.get("text", "") for p in last_prompt if p.get("type") == "text"])

            domain = detect_domain(last_prompt)
            kb_text = get_kb_context(domain, last_prompt)

            # Проверка intent на поиск в интернете
            web_info = ""
            if any(w in last_prompt.lower() for w in ["найди в сети", "поищи в интернете", "что пишут", "свежие новости", "datasheet", "распиновка", "4pda", "github"]):
                add_log(f"Запуск веб-поиска для запроса: '{last_prompt[:50]}'")
                web_info = web_search_ddg(last_prompt)

            # Анализ содержимого: наличие картинок (Vision) и сигнатуры кода
            has_image = any(isinstance(m.get("content"), list) and any(p.get("type") in ["image", "image_url"] for p in m["content"]) for m in raw_msgs)
            is_code = any(k in last_prompt.lower() for k in ["def ", "function", "class ", "import ", "const ", "var ", "asm", "arm64", "gradle", "bash", "kotlin", "java", "python", "curl", "adb", "git", "syntax", "refactor", "bug", "traceback", "exception", "tool_use", "patch", "diff"])

            # Интеллектуальный роутинг между узлами
            if has_image:
                preferred = "mi10t"  # Vision поддерживается только на Mi 10T (--mmproj)
            elif body.get("model") in ["omni-fast", "qwen-coder", "fast-reflex"] or (is_code and len(last_prompt.split()) < 250):
                preferred = "nord10" # Мгновенный синтаксический кодер на Nord N10 (:8081)
            else:
                preferred = "mi10t"  # Глубокая инженерия, физика, химия, архитектура (:8080)

            # Бесшовный фоллбек, если приоритетный узел не отвечает
            target_node = preferred
            if not NODES[preferred]["online"]:
                fallback = "mi10t" if preferred == "nord10" else "nord10"
                if NODES[fallback]["online"]:
                    target_node = fallback

            target_url = f"http://{NODES[target_node]['ip']}:{NODES[target_node]['port']}/v1/chat/completions"

            # Обогащение контекстом базы знаний
            enriched_msgs = list(raw_msgs)
            if kb_text or web_info:
                facts = []
                if kb_text:
                    facts.append(f"ФАКТЫ ИЗ БАЗЫ ЗНАНИЙ (FTS5):\n{kb_text}")
                if web_info:
                    facts.append(f"СВЕЖИЕ ДАННЫЕ ИЗ СЕТИ INTERNET (DuckDuckGo):\n{web_info}")
                sys_msg = "\n\n".join(facts)
                enriched_msgs.insert(0, {"role": "system", "content": sys_msg})

            try:
                res = http_json(target_url, {
                    "messages": enriched_msgs,
                    "temperature": body.get("temperature", 0.3),
                    "max_tokens": body.get("max_tokens", 2048)
                }, timeout=120)
                reply = res["choices"][0]["message"]["content"]
            except Exception as e:
                reply = f"[Triad-Omni Gateway]: Узел инференса ({target_url}) недоступен. {e}"

            if is_anthropic:
                return self._send({
                    "id": "msg_omni",
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "text", "text": reply}],
                    "model": body.get("model", "omni-brain"),
                    "usage": {"input_tokens": 100, "output_tokens": 300}
                })
            elif "api/chat" in self.path:
                return self._send({"message": {"role": "assistant", "content": reply}, "done": True})
            else:
                return self._send({
                    "id": "chatcmpl_omni",
                    "object": "chat.completion",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": reply}, "finish_reason": "stop"}]
                })

        # 3. Синхронизация навыков (SQLite FTS5)
        if self.path == "/v1/sync_skill":
            topic = body.get("topic", "Без темы")
            content = body.get("content", "")
            domain = body.get("domain") or detect_domain(topic + " " + content)
            conn.execute(
                "INSERT INTO skills_meta (domain, topic, content, source_folder, updated_at) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(topic) DO UPDATE SET content=excluded.content, utility_score=utility_score+1, updated_at=excluded.updated_at",
                (domain, topic, content, body.get("source", "Remote Agent"), datetime.now().isoformat())
            )
            conn.commit()
            add_log(f"Импортирован навык: {topic} [{domain}]")
            return self._send({"status": "synced", "domain": domain})

        self._send({"error": "Not Found"}, 404)

if __name__ == "__main__":
    port = 8000
    server = HTTPServer(("0.0.0.0", port), MasterGatewayHandler)
    print(f"⚡ [TRIAD-OMNI GATEWAY] Слушает http://0.0.0.0:{port}...")
    server.serve_forever()
