# -*- coding: utf-8 -*-
import os, json

apple_html = """<!DOCTYPE html>
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

with open('d:/для one plus nord n10/omni_gateway.py', 'r', encoding='utf-8') as f:
    code = f.read()

start_marker = 'DASHBOARD_HTML = """'
end_marker = '"""\n\n# ----------------- HTTP REQUEST HANDLER -----------------'

start_idx = code.find(start_marker)
end_idx = code.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_code = code[:start_idx] + 'DASHBOARD_HTML = """' + apple_html + '"""\n\n# ----------------- HTTP REQUEST HANDLER -----------------' + code[end_idx + len(end_marker):]
    with open('d:/для one plus nord n10/omni_gateway.py', 'w', encoding='utf-8') as f:
        f.write(new_code)
    print('SUCCESS: Apple-style UI injected into omni_gateway.py!')
else:
    print('ERROR: Markers not found! start_idx:', start_idx, 'end_idx:', end_idx)
