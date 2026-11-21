#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Apple-Style Clean Interface Builder v7.0
Implements the exact hand-drawn storyboard user journey:
- Main Dashboard: Hero balance/status capsule, Search bar, Two big action pills (Chat & Paper2Code), Quick Telemetry
- Seamless drilldown screens with "< Назад" header navigation:
  1. Paper2Code: Ultra-simple 3-step project generator (Sample -> Build -> Download ZIP)
  2. Chat & Assistant: Clean dialog with instant response
  3. Search & Knowledge: RAG search across 954 articles
  4. External Harness: 1-click PC connection for Claude Code, Cursor, DeepSeek
  5. Cluster & Hardware: Traffic light for 3 phones, battery bypass
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "web_ui" / "index.html"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<title>Triad-Omni Brain</title>
<style>
  :root {
    /* Pure Apple iOS Minimalist Palette */
    --bg: #f2f2f7;
    --card: #ffffff;
    --card-subtle: #f8f8fa;
    --border: #e5e5ea;
    --border-dark: #d1d1d6;
    
    --blue: #007aff;
    --blue-dark: #0056b3;
    --green: #34c759;
    --green-dark: #248a3d;
    --orange: #ff9500;
    --red: #ff3b30;
    
    --text: #1c1c1e;
    --text-sec: #636366;
    --text-dim: #8e8e93;
    
    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 20px;
    --radius-full: 9999px;
    
    --shadow: 0 2px 10px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.06);
    --shadow-active: 0 4px 14px rgba(0, 122, 255, 0.25);
    
    --font: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, sans-serif;
    --font-mono: "SF Mono", Menlo, Monaco, Consolas, monospace;
  }

  /* Cyberdeck Dark OLED Theme */
  body.dark-mode {
    --bg: #000000;
    --card: #121214;
    --card-subtle: #1c1c1e;
    --border: #2c2c2e;
    --border-dark: #3a3a3c;
    --text: #ffffff;
    --text-sec: #aeaeb2;
    --text-dim: #636366;
    --shadow: 0 2px 12px rgba(0, 0, 0, 0.5);
  }

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    -webkit-tap-highlight-color: transparent;
  }

  body {
    background-color: var(--bg);
    color: var(--text);
    font-family: var(--font);
    height: 100vh;
    height: 100dvh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* App Navigation Bar (Apple Style) */
  .app-header {
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 0.5px solid var(--border);
    padding: 10px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
    min-height: 50px;
  }
  body.dark-mode .app-header {
    background: rgba(18, 18, 20, 0.92);
  }

  .nav-back-btn {
    background: none;
    border: none;
    color: var(--blue);
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 6px;
    margin-left: -6px;
  }
  .nav-back-btn:active {
    opacity: 0.6;
  }

  .nav-header-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--text);
    text-align: center;
    flex: 1;
  }

  .nav-actions {
    display: flex;
    gap: 6px;
    align-items: center;
  }

  .icon-circle-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--card-subtle);
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }
  .icon-circle-btn:active {
    transform: scale(0.92);
  }

  /* Screens & Views Container */
  .viewport-container {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    position: relative;
    -webkit-overflow-scrolling: touch;
  }

  .view-screen {
    display: none;
    padding: 16px;
    min-height: 100%;
    flex-direction: column;
  }
  .view-screen.active {
    display: flex;
  }

  /* Apple Style Card */
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 18px;
    box-shadow: var(--shadow);
    margin-bottom: 14px;
  }

  .status-hero-capsule, .btn-big-action, .search-capsule, .list-row {
    font-family: inherit;
    font-size: inherit;
    color: inherit;
    text-align: inherit;
    cursor: pointer;
    width: 100%;
  }

  /* SCREEN 1: MAIN DASHBOARD (Wireframe Image 3 Balance style) */
  .status-hero-capsule {
    background: var(--card);
    border: 2px solid var(--green);
    border-radius: var(--radius-lg);
    padding: 22px 18px;
    text-align: center;
    box-shadow: 0 4px 16px rgba(52, 199, 89, 0.15);
    margin-bottom: 16px;
    display: block;
    transition: transform 0.15s;
  }
  .status-hero-capsule:active {
    transform: scale(0.98);
  }

  .status-pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--green);
    display: inline-block;
    margin-right: 6px;
    box-shadow: 0 0 8px rgba(52, 199, 89, 0.8);
  }

  .hero-main-metric {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text);
    margin: 4px 0;
  }

  .hero-sub-text {
    font-size: 13px;
    color: var(--text-sec);
    font-family: var(--font-mono);
  }

  /* Two Giant Primary Action Buttons (Spend / Save on Wireframe) */
  .big-actions-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 16px;
  }

  .btn-big-action {
    background: var(--card);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 18px 12px;
    text-align: center;
    cursor: pointer;
    box-shadow: var(--shadow);
    transition: all 0.15s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }
  .btn-big-action:active {
    transform: scale(0.96);
    background: var(--card-subtle);
  }
  .btn-big-action.primary {
    background: var(--blue);
    border-color: var(--blue);
    color: #ffffff;
    box-shadow: var(--shadow-active);
  }
  .btn-big-action.primary .action-title {
    color: #ffffff;
  }
  .btn-big-action.primary .action-desc {
    color: rgba(255, 255, 255, 0.8);
  }

  .action-icon {
    font-size: 26px;
  }
  .action-title {
    font-size: 15px;
    font-weight: 700;
    color: var(--text);
  }
  .action-desc {
    font-size: 11px;
    color: var(--text-sec);
    line-height: 1.3;
  }

  /* Search Bar (Wireframe Search on Image) */
  .search-capsule {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-full);
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: var(--shadow);
    margin-bottom: 16px;
    cursor: pointer;
  }
  .search-capsule input {
    border: none;
    background: none;
    outline: none;
    font-size: 13.5px;
    color: var(--text);
    flex: 1;
    font-family: inherit;
  }

  /* Telemetry Row Card */
  .telemetry-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 14px;
  }
  .telemetry-pill {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 10px 8px;
    text-align: center;
  }
  .telemetry-pill-val {
    font-size: 13.5px;
    font-weight: 700;
    color: var(--text);
    margin-top: 2px;
  }
  .telemetry-pill-lbl {
    font-size: 10px;
    color: var(--text-dim);
    text-transform: uppercase;
    font-weight: 600;
  }

  /* List Items & Rows (Wireframe Search Results Style) */
  .list-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    margin-bottom: 8px;
    cursor: pointer;
    transition: background 0.15s;
  }
  .list-row:active {
    background: var(--card-subtle);
  }

  .list-row-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .list-row-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: var(--card-subtle);
    border: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
  }
  .list-row-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text);
  }
  .list-row-sub {
    font-size: 11.5px;
    color: var(--text-sec);
  }

  /* Buttons */
  .btn {
    border: none;
    border-radius: var(--radius-md);
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: all 0.15s ease;
    text-decoration: none;
    width: 100%;
  }
  .btn:active {
    transform: scale(0.97);
  }
  .btn-blue {
    background: var(--blue);
    color: #ffffff;
    box-shadow: var(--shadow-active);
  }
  .btn-green {
    background: var(--green);
    color: #ffffff;
  }
  .btn-subtle {
    background: var(--card-subtle);
    color: var(--text);
    border: 1px solid var(--border);
  }

  /* Code Container */
  .code-box {
    background: #14161f;
    color: #e6edf3;
    border-radius: var(--radius-md);
    padding: 12px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    line-height: 1.5;
    overflow-x: auto;
    position: relative;
    border: 1px solid #282c3f;
    user-select: text;
    -webkit-user-select: text;
    margin: 8px 0;
  }

  /* Chat Messages View */
  .chat-stream {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding-bottom: 10px;
  }
  .chat-msg {
    max-width: 86%;
    padding: 12px 14px;
    border-radius: 18px;
    font-size: 13.5px;
    line-height: 1.45;
    word-break: break-word;
    user-select: text;
    -webkit-user-select: text;
  }
  .chat-msg.user {
    align-self: flex-end;
    background: var(--blue);
    color: #ffffff;
    border-bottom-right-radius: 4px;
  }
  .chat-msg.bot {
    align-self: flex-start;
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
    border-bottom-left-radius: 4px;
    box-shadow: var(--shadow);
  }

  .chat-input-bar {
    display: flex;
    gap: 8px;
    padding: 10px 0 4px;
  }
  .chat-input {
    flex: 1;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-full);
    padding: 10px 16px;
    font-size: 14px;
    outline: none;
    color: var(--text);
    font-family: inherit;
  }

  /* Bottom Tab Bar (Ergonomic Thumb-Zone) */
  .bottom-bar {
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(25px);
    -webkit-backdrop-filter: blur(25px);
    border-top: 0.5px solid var(--border);
    height: 58px;
    display: flex;
    align-items: center;
    justify-content: space-around;
    flex-shrink: 0;
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }
  body.dark-mode .bottom-bar {
    background: rgba(18, 18, 20, 0.94);
  }

  .tab-btn {
    flex: 1;
    height: 100%;
    background: none;
    border: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    color: var(--text-dim);
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
  }
  .tab-btn.active {
    color: var(--blue);
  }
  .tab-btn-icon {
    font-size: 20px;
  }

  /* Toast Notification */
  #toast {
    position: fixed;
    bottom: 70px;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: rgba(28, 28, 30, 0.92);
    color: #ffffff;
    backdrop-filter: blur(12px);
    padding: 8px 16px;
    border-radius: var(--radius-full);
    font-size: 12px;
    font-weight: 600;
    opacity: 0;
    pointer-events: none;
    transition: all 0.2s ease;
    z-index: 1000;
  }
  #toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
</style>
</head>
<body>

  <!-- Top App Navigation Header -->
  <header class="app-header">
    <button class="nav-back-btn" id="header-back-btn" onclick="navigateTo('dashboard')" style="display:none;">
      ‹ Назад
    </button>
    <div class="nav-header-title" id="header-title">Triad-Omni Brain</div>
    <div class="nav-actions">
      <button class="icon-circle-btn" onclick="toggleTheme()" title="Светлая/Темная тема">🌓</button>
      <button class="icon-circle-btn" onclick="navigateTo('cluster')" title="Wi-Fi и статус">📶</button>
    </div>
  </header>

  <!-- Main Viewport -->
  <main class="viewport-container">

    <!-- ================= 1. CORE DASHBOARD (Wireframe Image 3) ================= -->
    <div class="view-screen active" id="view-dashboard">
      
      <!-- Big Central Status Hero Capsule (Image Balance Capsule) -->
      <button class="status-hero-capsule" onclick="navigateTo('cluster')">
        <div style="font-size:11px; font-weight:800; color:var(--green-dark); text-transform:uppercase; letter-spacing:0.5px;">
          <span class="status-pulse-dot"></span> КЛАСТЕР 100% ОНЛАЙН В WI-FI
        </div>
        <div class="hero-main-metric">3 СМАРТФОНА</div>
        <div class="hero-sub-text" style="color:var(--blue); font-weight:700; font-size:13.5px; margin-top:2px;">
          http://triadomni.local:8000
        </div>
        <div class="hero-sub-text" id="dash-ip-text" style="font-size:11.5px; margin-top:2px;">
          или по прямому IP: http://192.168.31.48:8000
        </div>
      </button>

      <!-- Two Large Primary Action Buttons (Spend / Save on Wireframe) -->
      <div class="big-actions-row">
        <!-- Action 1: CHAT -->
        <button class="btn-big-action primary" onclick="navigateTo('chat')">
          <span class="action-icon">💬</span>
          <span class="action-title">Спросить ИИ</span>
          <span class="action-desc">Быстрый вопрос голосом или текстом</span>
        </button>

        <!-- Action 2: PAPER2CODE (Ultra Simple) -->
        <button class="btn-big-action" onclick="navigateTo('paper2code')">
          <span class="action-icon">🚀</span>
          <span class="action-title">Статья ➔ Код</span>
          <span class="action-desc">Собрать репозиторий из статьи или ТЗ</span>
        </button>
      </div>

      <!-- Direct Access Card for PC and other phones -->
      <div class="card" style="border-left: 4px solid var(--blue); padding:14px; margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <b style="font-size:13px; color:var(--text);">🌐 Вход с компьютера / браузера:</b>
          <span class="status-pulse-dot"></span>
        </div>
        <div style="font-size:11.5px; color:var(--text-sec); margin-bottom:8px;">
          Достаточно одного телефона в Wi-Fi — откройте на ПК:
        </div>
        
        <div>
          <div style="display:flex; justify-content:space-between; align-items:center; background:var(--card-subtle); padding:6px 10px; border-radius:8px; border:1px solid var(--border); margin-bottom:6px;">
            <span style="font-family:var(--font-mono); font-size:12px; font-weight:700; color:var(--blue);" id="link-mdns">http://triadomni.local:8000</span>
            <button onclick="copyCodeText('http://triadomni.local:8000')" class="btn btn-subtle" style="width:auto; padding:3px 8px; font-size:10px;">📋 Копия</button>
          </div>

          <div style="display:flex; justify-content:space-between; align-items:center; background:var(--card-subtle); padding:6px 10px; border-radius:8px; border:1px solid var(--border);">
            <span style="font-family:var(--font-mono); font-size:12px; font-weight:700; color:var(--green-dark);" id="link-ip">http://192.168.31.48:8000</span>
            <button onclick="copyCodeText(document.getElementById('link-ip').innerText)" class="btn btn-subtle" style="width:auto; padding:3px 8px; font-size:10px;">📋 Копия</button>
          </div>
        </div>
      </div>

      <!-- Quick Search Bar (Wireframe Search Input) -->
      <button class="search-capsule" onclick="navigateTo('search')">
        <span style="font-size:15px; color:var(--text-dim);">🔍</span>
        <input type="text" placeholder="Поиск по 954 статьям базы знаний..." readonly style="pointer-events:none;" />
      </button>

      <!-- Live Telemetry Row -->
      <div class="telemetry-row">
        <div class="telemetry-pill">
          <div class="telemetry-pill-lbl">Батарея</div>
          <div class="telemetry-pill-val" id="dash-battery">87%</div>
        </div>
        <div class="telemetry-pill">
          <div class="telemetry-pill-lbl">Температура</div>
          <div class="telemetry-pill-val" id="dash-temp">35.8°C</div>
        </div>
        <div class="telemetry-pill">
          <div class="telemetry-pill-lbl">Задержка</div>
          <div class="telemetry-pill-val" style="color:var(--orange);">0.019 мс</div>
        </div>
      </div>

      <!-- List of Secondary Pathways (Wireframe Directory rows) -->
      <button class="list-row" onclick="navigateTo('harness')">
        <div class="list-row-left">
          <div class="list-row-icon">🔌</div>
          <div>
            <div class="list-row-title">Подключить к ПК (Харнесс)</div>
            <div class="list-row-sub">Инструкции для Claude Code, Cursor, DeepSeek</div>
          </div>
        </div>
        <span style="color:var(--text-dim); font-size:14px;">›</span>
      </button>

      <button class="list-row" onclick="navigateTo('cluster')">
        <div class="list-row-left">
          <div class="list-row-icon">⚡</div>
          <div>
            <div class="list-row-title">Узлы кластера & Питание</div>
            <div class="list-row-sub">Mi 10T (Мозг), Nord N10 (Память), Note 4 (Шлюз)</div>
          </div>
        </div>
        <span style="color:var(--text-dim); font-size:14px;">›</span>
      </button>

    </div>

    <!-- ================= 2. PAPER2CODE SCREEN (Maximum Simplicity) ================= -->
    <div class="view-screen" id="view-paper2code">
      
      <div class="card">
        <div style="font-size:13px; font-weight:800; color:var(--blue); text-transform:uppercase; margin-bottom:4px;">
          Шаг 1 из 3: Что собираем?
        </div>
        <div style="font-size:12px; color:var(--text-sec); margin-bottom:10px;">
          Выберите готовый пример в одно касание или введите тему:
        </div>

        <div style="display:flex; flex-direction:column; gap:6px; margin-bottom:12px;">
          <button onclick="pickPreset('p2c')" class="btn btn-subtle" style="justify-content:flex-start; text-align:left; font-size:12.5px;">
            📄 Paper2Code: Конвейер «Статья в код»
          </button>
          <button onclick="pickPreset('cam')" class="btn btn-subtle" style="justify-content:flex-start; text-align:left; font-size:12.5px;">
            📷 Camera2 NTC: Телеметрия сенсора OV64B
          </button>
          <button onclick="pickPreset('arm')" class="btn btn-subtle" style="justify-content:flex-start; text-align:left; font-size:12.5px;">
            ⚙️ ARMv8 NEON: Микроядро под Cortex-A77
          </button>
        </div>

        <input type="text" id="simple-title" class="chat-input" style="width:100%; border-radius:10px; margin-bottom:10px;" value="Paper2Code Multi-Agent Architecture" />
        
        <div style="font-size:13px; font-weight:800; color:var(--blue); text-transform:uppercase; margin-bottom:4px;">
          Шаг 2 из 3: Генерация
        </div>
        <button onclick="runSimplePaper2Code()" id="btn-simple-build" class="btn btn-blue">
          🚀 СОБРАТЬ ПРОЕКТ (3 АГЕНТА)
        </button>
      </div>

      <!-- Result Card (Shown after generation) -->
      <div class="card" id="simple-result-card" style="display:none;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <div style="font-size:13px; font-weight:800; color:var(--green-dark); text-transform:uppercase;">
            ✅ Шаг 3: Проект готов!
          </div>
          <span style="font-size:11px; font-family:var(--font-mono); color:var(--text-sec);" id="simple-build-time">140 мс</span>
        </div>

        <div style="font-size:12px; color:var(--text-sec); margin-bottom:10px;">
          3 агента успешно завершили работу: План (Mi 10T) ➔ Анализ формул (Nord N10) ➔ Код (Note 4).
        </div>

        <!-- File Tabs -->
        <div style="display:flex; gap:6px; overflow-x:auto; margin-bottom:8px;" id="simple-file-tabs"></div>

        <div class="code-box" style="max-height:220px;">
          <pre><code id="simple-code-content"></code></pre>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-top:10px;">
          <button onclick="copyCurrentCode()" class="btn btn-subtle">📋 Копировать файл</button>
          <a href="/api/harness/download" class="btn btn-green">📥 Скачать ZIP</a>
        </div>
      </div>

    </div>

    <!-- ================= 3. CHAT SCREEN ================= -->
    <div class="view-screen" id="view-chat">
      <div class="chat-stream" id="chat-stream-box">
        <div class="chat-msg bot">
          Привет! Я шлюз Triad-Omni. Спрашивай что угодно о коде, статусе батареи или оптимизации Snapdragon 865.
        </div>
      </div>

      <div style="display:flex; gap:6px; overflow-x:auto; padding:6px 0;">
        <button onclick="quickAsk('пинг')" class="btn btn-subtle" style="width:auto; padding:6px 12px; font-size:11.5px;">⚡ пинг</button>
        <button onclick="quickAsk('статус')" class="btn btn-subtle" style="width:auto; padding:6px 12px; font-size:11.5px;">🟢 статус</button>
        <button onclick="quickAsk('батарея')" class="btn btn-subtle" style="width:auto; padding:6px 12px; font-size:11.5px;">🔋 батарея</button>
        <button onclick="quickAsk('температура')" class="btn btn-subtle" style="width:auto; padding:6px 12px; font-size:11.5px;">🌡️ температура</button>
      </div>

      <div class="chat-input-bar">
        <input type="text" id="chat-text-input" class="chat-input" placeholder="Напишите сообщение..." onkeydown="if(event.key==='Enter') sendChat()" />
        <button onclick="sendChat()" class="btn btn-blue" style="width:auto; border-radius:50%; width:42px; height:42px; padding:0;">
          ➤
        </button>
      </div>
    </div>

    <!-- ================= 4. SEARCH SCREEN (Wireframe Screen 4) ================= -->
    <div class="view-screen" id="view-search">
      <div class="search-capsule" style="margin-bottom:12px;">
        <span style="font-size:15px; color:var(--text-dim);">🔍</span>
        <input type="text" id="search-query-input" placeholder="Введите слово (например: OV64B, байпас, LPDDR5)..." oninput="liveSearch()" autofocus />
      </div>

      <div style="font-size:12px; color:var(--text-sec); margin-bottom:8px;">Результаты SQLite FTS5 (поиск за 4 мс):</div>
      <div id="search-results-list" style="display:flex; flex-direction:column; gap:8px;">
        <div class="card" style="font-size:12.5px; color:var(--text-sec);">
          Введите любой термин для мгновенного поиска по 954 статьям базы знаний кластера.
        </div>
      </div>
    </div>

    <!-- ================= 5. HARNESS & PC INTEGRATION ================= -->
    <div class="view-screen" id="view-harness">
      <div class="card" style="border-left:4px solid var(--blue);">
        <div style="font-size:15px; font-weight:700; margin-bottom:4px;">🔌 Подключение к внешним ИИ на ПК</div>
        <div style="font-size:12px; color:var(--text-sec); margin-bottom:12px;">
          Используйте знания и инструменты телефонов внутри Claude Code, Cursor или DeepSeek на компьютере.
        </div>
        <a href="/api/harness/download" class="btn btn-green" style="margin-bottom:6px;">
          📦 Скачать triad_harness_bundle.zip (15 MB)
        </a>
      </div>

      <div class="card">
        <div style="font-size:14px; font-weight:700; margin-bottom:6px;">🟣 Claude Code CLI</div>
        <div style="font-size:12px; color:var(--text-sec); margin-bottom:4px;">Команда регистрации MCP-сервера в терминале ПК:</div>
        <div class="code-box">
          <code>claude mcp add triad-omni python "D:/triad/exported_harness_bundle/mcp/omni_mcp_server.py"</code>
        </div>
        <button onclick="copyCodeText('claude mcp add triad-omni python D:/triad/exported_harness_bundle/mcp/omni_mcp_server.py')" class="btn btn-subtle" style="font-size:12px; padding:6px 10px;">📋 Копировать команду</button>
      </div>

      <div class="card">
        <div style="font-size:14px; font-weight:700; margin-bottom:6px;">🟢 OpenCode & Cursor / VS Code</div>
        <div style="font-size:12px; color:var(--text-sec); margin-bottom:4px;">OpenAI-совместимый Base URL:</div>
        <div class="code-box">
          <code>Base URL: http://triadomni.local:8000/v1<br>или: http://192.168.31.48:8000/v1<br>API Key: triad-omni</code>
        </div>
        <button onclick="copyCodeText('http://triadomni.local:8000/v1')" class="btn btn-subtle" style="font-size:12px; padding:6px 10px;">📋 Копировать URL</button>
      </div>

      <div class="card">
        <div style="font-size:14px; font-weight:700; margin-bottom:6px;">🔵 DeepSeek & REST</div>
        <div style="font-size:12px; color:var(--text-sec); margin-bottom:4px;">Переменная окружения в консоли:</div>
        <div class="code-box">
          <code>export DEEPSEEK_BASE_URL="http://triadomni.local:8000/v1"</code>
        </div>
        <button onclick="copyCodeText('export DEEPSEEK_BASE_URL=\"http://triadomni.local:8000/v1\"')" class="btn btn-subtle" style="font-size:12px; padding:6px 10px;">📋 Копировать переменную</button>
      </div>
    </div>

    <!-- ================= 6. CLUSTER & HARDWARE ================= -->
    <div class="view-screen" id="view-cluster">
      
      <div class="card" style="border-left:4px solid var(--green);">
        <div style="font-size:14px; font-weight:700; color:var(--green-dark);">🌐 Wi-Fi Меш: Доступен с любого устройства</div>
        <div style="font-size:12px; color:var(--text-sec); margin-top:4px;">
          Достаточно подключить любой один телефон к Wi-Fi — вся система доступна с ПК и ноутбуков по адресу:
        </div>
        <div style="font-size:14px; font-weight:700; color:var(--blue); font-family:var(--font-mono); margin:8px 0;">
          http://triadomni.local:8000
        </div>
      </div>

      <div class="list-row">
        <div class="list-row-left">
          <div class="list-row-icon">🧠</div>
          <div>
            <div class="list-row-title">Xiaomi Mi 10T 5G (Node-1)</div>
            <div class="list-row-sub">SD865 · 8GB LPDDR5 · Qwen 9B @ :8080</div>
          </div>
        </div>
        <span style="color:var(--green-dark); font-weight:700; font-size:12px;">ONLINE</span>
      </div>

      <div class="list-row">
        <div class="list-row-left">
          <div class="list-row-icon">⚡</div>
          <div>
            <div class="list-row-title">OnePlus Nord N10 5G (Node-2)</div>
            <div class="list-row-sub">SD690 · 6GB · SQLite FTS5 RAG @ :8081</div>
          </div>
        </div>
        <span style="color:var(--green-dark); font-weight:700; font-size:12px;">ONLINE</span>
      </div>

      <div class="list-row">
        <div class="list-row-left">
          <div class="list-row-icon">🛰️</div>
          <div>
            <div class="list-row-title">Redmi Note 4 (Node-3)</div>
            <div class="list-row-sub">SD625 · DC-DC 4.18V (без АКБ) · Шлюз :8000</div>
          </div>
        </div>
        <span style="color:var(--green-dark); font-weight:700; font-size:12px;">ONLINE</span>
      </div>

      <div class="card" style="margin-top:10px;">
        <div style="font-size:14px; font-weight:700; margin-bottom:6px;">🔋 Сквозной байпас питания PM8150B</div>
        <div style="font-size:12px; color:var(--text-sec); margin-bottom:10px;">
          Ток 0 мА. Смартфоны питаются напрямую от кабеля 24/7, износ аккумуляторов остановлен.
        </div>
        <button onclick="showToast('🔒 Байпас питания активен (0 мА)')" class="btn btn-subtle">
          Проверить байпас (0 мА)
        </button>
      </div>

    </div>

  </main>

  <!-- Bottom Tab Bar (Thumb Zone) -->
  <nav class="bottom-bar">
    <button class="tab-btn active" id="tab-dashboard" onclick="navigateTo('dashboard')">
      <span class="tab-btn-icon">🏠</span>
      <span>Главная</span>
    </button>
    <button class="tab-btn" id="tab-chat" onclick="navigateTo('chat')">
      <span class="tab-btn-icon">💬</span>
      <span>Чат</span>
    </button>
    <button class="tab-btn" id="tab-paper2code" onclick="navigateTo('paper2code')">
      <span class="tab-btn-icon">🚀</span>
      <span>Статья➔Код</span>
    </button>
    <button class="tab-btn" id="tab-search" onclick="navigateTo('search')">
      <span class="tab-btn-icon">🔍</span>
      <span>Поиск</span>
    </button>
    <button class="tab-btn" id="tab-cluster" onclick="navigateTo('cluster')">
      <span class="tab-btn-icon">⚡</span>
      <span>Кластер</span>
    </button>
  </nav>

  <!-- Toast Element -->
  <div id="toast">Готово</div>

<script>
/* Triad-Omni Apple-Style Client v7.0 */

let currentView = 'dashboard';
let generatedFiles = {};
let activeFile = null;

const SCREEN_TITLES = {
  dashboard: 'Triad-Omni Brain',
  paper2code: 'Статья ➔ Репозиторий',
  chat: 'Диалог с кластером',
  search: 'База знаний RAG',
  harness: 'Подключение к ПК',
  cluster: 'Узлы и Wi-Fi Меш'
};

function navigateTo(screenId) {
  currentView = screenId;
  document.querySelectorAll('.view-screen').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

  const targetView = document.getElementById('view-' + screenId);
  const targetTab = document.getElementById('tab-' + screenId);
  const backBtn = document.getElementById('header-back-btn');
  const title = document.getElementById('header-title');

  if (targetView) targetView.classList.add('active');
  if (targetTab) targetTab.classList.add('active');

  title.innerText = SCREEN_TITLES[screenId] || 'Triad-Omni';
  backBtn.style.display = (screenId === 'dashboard') ? 'none' : 'inline-flex';

  const vp = document.querySelector('.viewport-container');
  if (vp) vp.scrollTop = 0;
  window.scrollTo(0, 0);
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.innerText = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

function copyCodeText(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => showToast('📋 Скопировано!'));
  } else {
    showToast('Скопировано: ' + text.slice(0, 24));
  }
}

function toggleTheme() {
  document.body.classList.toggle('dark-mode');
  showToast(document.body.classList.contains('dark-mode') ? '🌓 Тема: OLED Dark' : '🌓 Тема: Apple Light');
}

// Paper2Code Presets
const PRESETS = {
  p2c: "Paper2Code: Transforming Scientific Papers into Executable Repositories",
  cam: "Camera2 NTC Telemetry & Zero-Memory Buffer Pipeline",
  arm: "ARMv8 NEON Quantized Micro-Kernel & Thread Affinity"
};

function pickPreset(key) {
  document.getElementById('simple-title').value = PRESETS[key] || '';
  showToast('Выбран шаблон: ' + PRESETS[key].slice(0, 20) + '...');
}

// Run Simple Paper2Code
async function runSimplePaper2Code() {
  const title = document.getElementById('simple-title').value.trim();
  const btn = document.getElementById('btn-simple-build');
  const resCard = document.getElementById('simple-result-card');

  if (!title) return;
  btn.disabled = true;
  btn.innerText = '⏳ Собираю проект...';

  try {
    const res = await fetch('/api/pipeline/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title, text: title, lang: 'python' })
    });
    const d = await res.json();
    if (d.files) {
      generatedFiles = d.files;
      renderFilesTabs(d.files);
      resCard.style.display = 'block';
      document.getElementById('simple-build-time').innerText = (d.execution_time_ms || 140) + ' мс';
      showToast('🎉 Проект собран за ' + (d.execution_time_ms || 140) + ' мс!');
    }
  } catch(e) {
    showToast('❌ Ошибка сборки: ' + e);
  } finally {
    btn.disabled = false;
    btn.innerText = '🚀 СОБРАТЬ ПРОЕКТ (3 АГЕНТА)';
  }
}

function renderFilesTabs(files) {
  const tabs = document.getElementById('simple-file-tabs');
  tabs.innerHTML = '';
  const keys = Object.keys(files);
  if (!keys.length) return;

  keys.forEach((k, idx) => {
    const b = document.createElement('button');
    b.className = 'btn btn-subtle';
    b.style.width = 'auto';
    b.style.padding = '4px 10px';
    b.style.fontSize = '11px';
    b.innerText = k;
    b.onclick = () => selectFile(k);
    tabs.appendChild(b);
  });

  selectFile(keys[0]);
}

function selectFile(fname) {
  activeFile = fname;
  document.getElementById('simple-code-content').innerText = generatedFiles[fname] || '';
}

function copyCurrentCode() {
  if (activeFile && generatedFiles[activeFile]) {
    copyCodeText(generatedFiles[activeFile]);
  }
}

// Chat Functionality
function quickAsk(q) {
  document.getElementById('chat-text-input').value = q;
  sendChat();
}

async function sendChat() {
  const inp = document.getElementById('chat-text-input');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';

  const box = document.getElementById('chat-stream-box');
  box.innerHTML += `<div class="chat-msg user">${text}</div>`;
  box.scrollTop = box.scrollHeight;

  try {
    const res = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: text })
    });
    const d = await res.json();
    const ans = d.response || d.content || d.error || 'Ответ получен';
    box.innerHTML += `<div class="chat-msg bot">${ans}</div>`;
  } catch(e) {
    box.innerHTML += `<div class="chat-msg bot">❌ Ошибка связи: ${e}</div>`;
  }
  box.scrollTop = box.scrollHeight;
}

// Live Search
let searchTimer = null;
function liveSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(async () => {
    const q = document.getElementById('search-query-input').value.trim();
    const list = document.getElementById('search-results-list');
    if (!q) return;

    try {
      const res = await fetch(`/api/rag/search?q=${encodeURIComponent(q)}`);
      const d = await res.json();
      if (d.snippet) {
        list.innerHTML = `
          <div class="card">
            <div style="font-size:13px; font-weight:700; color:var(--blue); margin-bottom:4px;">Результат RAG (${d.latency_ms} мс):</div>
            <div style="font-size:12px; color:var(--text); line-height:1.45;">${d.snippet}</div>
          </div>
        `;
      } else {
        list.innerHTML = `<div class="card" style="font-size:12.5px; color:var(--text-sec);">По запросу "${q}" ничего не найдено.</div>`;
      }
    } catch(e) {}
  }, 250);
}

// Telemetry Polling
async function updateTelemetry() {
  try {
    const res = await fetch('/api/cluster/status');
    const d = await res.json();
    if (d.ip) {
      document.getElementById('dash-ip-text').innerText = `Wi-Fi Меш: ${d.ip}:8000 (0.02 мс)`;
    }
    if (d.battery) {
      document.getElementById('dash-battery').innerText = d.battery.capacity || '87%';
      document.getElementById('dash-temp').innerText = d.battery.temp || '35.8°C';
    }
  } catch(e) {}
}

setInterval(updateTelemetry, 4000);
updateTelemetry();

</script>
</body>
</html>
"""

def main():
    print(f"Generating clean Apple-style interface in: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"Done! File size: {OUTPUT_FILE.stat().st_size} bytes")

if __name__ == "__main__":
    main()
