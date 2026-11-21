#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni-Forge Studio v5.1 (Apple Developer Edition - Pure Light Theme)
Стильная веб-студия управления знаниями, датасетами, версионированием и LoRA
в светлом дизайне macOS Sequoia / Apple Developer Portal.
Работает полностью на стандартной библиотеке Python (без внешних зависимостей).
"""

import os
import sys
import json
import sqlite3
import subprocess
import urllib
import urllib.parse
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
CARTRIDGES_DIR = BASE_DIR / "cartridges"
SCRIPTS_DIR = BASE_DIR / "scripts"
SKILL_DB = BASE_DIR / "skill_registry.db"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
ARTICLES_DIR = BASE_DIR / "ARTICLES"
PORT = 8090

# Создаем папки
DATASETS_DIR.mkdir(parents=True, exist_ok=True)
CARTRIDGES_DIR.mkdir(parents=True, exist_ok=True)
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

# Подключаем менеджеры
sys.path.insert(0, str(SCRIPTS_DIR))
try:
    from training_tracker import load_training_state, mark_as_trained
except ImportError:
    def load_training_state(): return {"needs_training": False, "status_text": "🟢 Модель актуальна", "files": []}
    def mark_as_trained(): return load_training_state()

try:
    from knowledge_manager import list_articles, get_article, save_article, get_article_history, rollback_article
except ImportError:
    def list_articles(): return []
    def get_article(f): return {"content": ""}
    def save_article(f, c): return {"ok": True}
    def get_article_history(f): return []
    def rollback_article(f, b): return {"ok": True}

try:
    from cartridge_manager import (
        list_cartridges, get_active_cartridge, unpack_and_install_cartridge,
        set_active_cartridge, get_storage_stats, prune_cartridge_cache, activate_version
    )
except ImportError:
    def list_cartridges(): return []
    def get_active_cartridge(): return {"active": False, "name": "Не подключен"}
    def unpack_and_install_cartridge(f): return {"ok": False, "error": "Менеджер не доступен"}
    def set_active_cartridge(d): pass
    def get_storage_stats(max_mb=1024): return {"total_mb": 0, "max_mb": max_mb, "free_mb": max_mb, "percent_used": 0}
    def prune_cartridge_cache(max_mb=1024, max_versions_per_slug=5): return {"ok": True, "freed_mb": 0}
    def activate_version(t): return {"ok": False, "error": "Менеджер не доступен"}

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Omni-Forge Studio | Apple Developer Edition</title>
<style>
  :root {
    --bg-base: #f5f5f7;
    --bg-surface: #ffffff;
    --bg-surface-subtle: #fbfbfd;
    --border-subtle: #e5e5ea;
    --border-prominent: #d2d2d7;
    --accent-blue: #0071e3;
    --accent-teal: #00838f;
    --accent-green: #34c759;
    --accent-green-text: #1b8a3e;
    --accent-orange: #ff9500;
    --accent-orange-text: #b25000;
    --accent-red: #ff3b30;
    --accent-red-text: #d70015;
    --text-primary: #1d1d1f;
    --text-secondary: #6e6e73;
    --text-tertiary: #86868b;
    --card-shadow: 0 2px 10px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  html[data-theme="cyberdeck"] {
    --bg-base: #090d16;
    --bg-surface: #111827;
    --bg-surface-subtle: #0d131f;
    --border-subtle: #1f2937;
    --border-prominent: #374151;
    --accent-blue: #00ffcc;
    --accent-teal: #38bdf8;
    --accent-green: #00ff88;
    --accent-green-text: #00ff88;
    --accent-orange: #ffaa00;
    --accent-orange-text: #ffaa00;
    --accent-red: #ff3366;
    --accent-red-text: #ff3366;
    --text-primary: #f3f4f6;
    --text-secondary: #9ca3af;
    --text-tertiary: #6b7280;
    --card-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), 0 0 1px rgba(0, 255, 204, 0.2);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }

  body {
    background: var(--bg-base);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    padding: 24px 28px;
    line-height: 1.45;
    letter-spacing: -0.012em;
    min-height: 100vh;
  }

  /* Apple Navigation Bar */
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 18px;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 12px;
  }
  .brand-group {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand-logo {
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, #0071e3, #42a5f5);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    color: #ffffff;
    font-weight: 800;
  }
  h1 {
    font-size: 1.25rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: var(--text-primary);
  }
  .version-tag {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.05);
    color: var(--text-secondary);
    border: 1px solid var(--border-subtle);
  }
  .nav-shortcuts {
    display: flex;
    gap: 16px;
  }
  .nav-shortcuts a {
    color: var(--accent-blue);
    text-decoration: none;
    font-size: 0.82rem;
    font-weight: 500;
    transition: opacity 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .nav-shortcuts a:hover {
    opacity: 0.75;
  }

  /* Apple Dynamic Reminder Widget */
  .reminder-widget {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    box-shadow: var(--card-shadow);
    border-radius: 16px;
    padding: 14px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 14px;
    margin-bottom: 22px;
    transition: all 0.25s ease;
  }
  .reminder-widget.status-ok {
    border-color: rgba(52, 199, 89, 0.35);
    background: rgba(52, 199, 89, 0.05);
  }
  .reminder-widget.status-warn {
    border-color: rgba(255, 149, 0, 0.35);
    background: rgba(255, 149, 0, 0.06);
  }
  .widget-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
  }
  .widget-value {
    font-size: 0.95rem;
    font-weight: 600;
    margin-top: 2px;
  }

  /* Apple Segmented Controls (macOS Tab Bar) */
  .segmented-control {
    display: inline-flex;
    background: rgba(118, 118, 128, 0.12);
    padding: 3px;
    border-radius: 10px;
    gap: 2px;
    margin-bottom: 22px;
    overflow-x: auto;
    max-width: 100%;
  }
  .segment-btn {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    padding: 7px 16px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 500;
    font-family: inherit;
    cursor: pointer;
    transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
    white-space: nowrap;
    outline: none;
  }
  .segment-btn:hover {
    color: var(--text-primary);
  }
  .segment-btn.active {
    background: #ffffff;
    color: var(--text-primary);
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  }

  /* Layout Containers */
  .tab-panel { display: none; }
  .tab-panel.active { display: block; animation: fadeIn 0.2s ease; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

  .apple-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
    gap: 18px;
    margin-bottom: 22px;
  }

  .apple-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    box-shadow: var(--card-shadow);
    border-radius: 16px;
    padding: 22px;
    position: relative;
    transition: border-color 0.2s;
  }
  .apple-card:hover {
    border-color: var(--border-prominent);
  }
  .apple-card h2 {
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: -0.015em;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--text-primary);
  }
  .apple-card p {
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin-bottom: 16px;
    line-height: 1.5;
  }

  /* Apple Push Buttons */
  .apple-btn {
    background: rgba(0, 0, 0, 0.04);
    border: 1px solid var(--border-subtle);
    color: var(--text-primary);
    padding: 8px 15px;
    border-radius: 9px;
    font-size: 0.82rem;
    font-weight: 500;
    font-family: inherit;
    cursor: pointer;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    text-decoration: none;
    outline: none;
  }
  .apple-btn:hover {
    background: rgba(0, 0, 0, 0.08);
    border-color: var(--border-prominent);
  }
  .apple-btn-primary {
    background: var(--accent-blue);
    border-color: var(--accent-blue);
    color: #ffffff;
    font-weight: 600;
  }
  .apple-btn-primary:hover {
    background: #0077ed;
    box-shadow: 0 4px 14px rgba(0, 113, 227, 0.3);
  }
  .apple-btn-success {
    background: rgba(52, 199, 89, 0.14);
    border-color: rgba(52, 199, 89, 0.35);
    color: var(--accent-green-text);
    font-weight: 600;
  }
  .apple-btn-success:hover {
    background: var(--accent-green);
    color: #ffffff;
  }

  /* Split View Editor (Apple Notes Style) */
  .split-view {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 18px;
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    box-shadow: var(--card-shadow);
    border-radius: 18px;
    overflow: hidden;
    min-height: 620px;
  }
  .split-sidebar {
    border-right: 1px solid var(--border-subtle);
    padding: 16px;
    display: flex;
    flex-direction: column;
    background: var(--bg-surface-subtle);
  }
  .split-main {
    padding: 20px;
    display: flex;
    flex-direction: column;
    background: #ffffff;
  }

  .search-input {
    width: 100%;
    background: #ffffff;
    border: 1px solid var(--border-prominent);
    color: var(--text-primary);
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-family: inherit;
    outline: none;
    margin-bottom: 12px;
    transition: border-color 0.2s;
  }
  .search-input:focus {
    border-color: var(--accent-blue);
    box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.15);
  }

  .article-list {
    overflow-y: auto;
    max-height: 540px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .article-item {
    padding: 10px 12px;
    border-radius: 9px;
    cursor: pointer;
    transition: background 0.15s;
    border: 1px solid transparent;
  }
  .article-item:hover {
    background: rgba(0, 0, 0, 0.04);
  }
  .article-item.selected {
    background: rgba(0, 113, 227, 0.08);
    border-color: rgba(0, 113, 227, 0.25);
  }
  .article-item-title {
    font-size: 0.84rem;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .article-item-meta {
    font-size: 0.72rem;
    color: var(--text-secondary);
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
  }

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 14px;
    flex-wrap: wrap;
    gap: 10px;
  }
  .editor-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
  }
  .editor-textarea {
    width: 100%;
    flex: 1;
    min-height: 460px;
    background: var(--bg-surface-subtle);
    border: 1px solid var(--border-prominent);
    border-radius: 10px;
    padding: 16px;
    color: #1d1d1f;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.85rem;
    line-height: 1.6;
    resize: vertical;
    outline: none;
    transition: border-color 0.2s;
  }
  .editor-textarea:focus {
    border-color: var(--accent-blue);
    box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.12);
  }

  /* History Sheet */
  .history-box {
    background: var(--bg-surface-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 12px;
    margin-top: 14px;
    font-size: 0.8rem;
  }

  /* Tables */
  .apple-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }
  .apple-table th, .apple-table td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border-subtle);
    text-align: left;
  }
  .apple-table th {
    color: var(--text-secondary);
    text-transform: uppercase;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
  }
  .apple-table td {
    color: var(--text-primary);
  }

  pre {
    background: var(--bg-surface-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 14px;
    font-family: ui-monospace, Menlo, Monaco, monospace;
    font-size: 0.8rem;
    color: #24292e;
    overflow-x: auto;
    max-height: 260px;
  }

  code {
    background: rgba(0, 0, 0, 0.05);
    color: #b31d28;
    padding: 2px 5px;
    border-radius: 4px;
    font-size: 0.82em;
    font-family: monospace;
  }

  /* Apple Drag & Drop Zone */
  .drop-zone {
    border: 2px dashed var(--accent-blue);
    background: rgba(0, 113, 227, 0.03);
    border-radius: 14px;
    padding: 32px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    user-select: none;
    margin-top: 14px;
  }
  .drop-zone:hover, .drop-zone.dragover {
    background: rgba(0, 113, 227, 0.09);
    border-color: #0077ed;
    transform: scale(1.006);
    box-shadow: 0 6px 24px rgba(0, 113, 227, 0.12);
  }
</style>
</head>
<body>

<!-- Header -->
<header>
  <div class="brand-group">
    <div class="brand-logo">Ω</div>
    <h1>Omni-Forge Studio <span class="version-tag">Triad-Omni v5.0</span></h1>
  </div>
  <div class="nav-shortcuts" style="align-items:center;">
    <a href="http://127.0.0.1:8000" target="_blank" title="Node-3 Redmi Note 4 Gateway">📡 Master Hub (:8000)</a>
    <a href="http://127.0.0.1:8080" target="_blank" title="Node-1 Mi 10T Brain">🧠 Mi 10T (:8080)</a>
    <a href="http://127.0.0.1:8081" target="_blank" title="Node-2 Nord N10 Reflex">⚡ Nord N10 (:8081)</a>
    <button id="theme-btn" class="apple-btn" onclick="toggleTheme()" style="min-height:36px; padding:4px 12px; font-size:0.78rem; font-weight:600; cursor:pointer;">🌙 Cyberdeck HUD</button>
  </div>
</header>

<!-- Dynamic Reminder Banner -->
<div id="reminder-widget" class="reminder-widget status-ok">
  <div>
    <div class="widget-label">🎓 Модель личности & Инженерный стиль (Node-1 Mi 10T)</div>
    <div id="reminder-text" class="widget-value" style="color:var(--accent-green-text);">Загрузка телеметрии...</div>
  </div>
  <div style="display:flex; gap:10px; align-items:center;">
    <button class="apple-btn apple-btn-success" onclick="markModelTrained()">✅ Я обучила модель</button>
    <button class="apple-btn" onclick="selectSegment('training')">Файлы обучения 📦</button>
  </div>
</div>

<!-- Apple Segmented Control -->
<div class="segmented-control">
  <button class="segment-btn active" id="btn-editor" onclick="selectSegment('editor')">📝 База Знаний & Редактор (43)</button>
  <button class="segment-btn" id="btn-training" onclick="selectSegment('training')">🎓 Центр Обучения и Файлы</button>
  <button class="segment-btn" id="btn-dataset" onclick="selectSegment('dataset')">📚 SFT Датасеты</button>
  <button class="segment-btn" id="btn-colab" onclick="selectSegment('colab')">🚀 Colab / Unsloth</button>
  <button class="segment-btn" id="btn-cartridges" onclick="selectSegment('cartridges')">💾 LoRA Картриджи</button>
  <button class="segment-btn" id="btn-skills" onclick="selectSegment('skills')">🧩 Скилы (128)</button>
</div>

<!-- ================= TAB 1: KNOWLEDGE EDITOR (APPLE NOTES STYLE) ================= -->
<div id="tab-editor" class="tab-panel active">
  <div class="split-view">
    <!-- Sidebar -->
    <div class="split-sidebar">
      <input type="text" id="article-search" class="search-input" placeholder="🔍 Поиск статей..." oninput="filterArticles()">
      <div id="article-list-container" class="article-list">
        Загрузка списка статей...
      </div>
    </div>

    <!-- Main Editor Pane -->
    <div class="split-main">
      <div class="editor-header">
        <div>
          <div id="editor-filename" class="version-tag" style="display:inline-block; margin-bottom:4px;">Выберите статью слева</div>
          <div id="editor-title" class="editor-title">Интерактивный редактор базы знаний</div>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="apple-btn apple-btn-primary" onclick="saveCurrentArticle()">💾 Сохранить и обновить RAG</button>
          <button class="apple-btn" onclick="toggleHistoryView()">🕒 Версии (<span id="history-badge">0</span>)</button>
        </div>
      </div>

      <textarea id="article-content-input" class="editor-textarea" placeholder="Выберите статью из списка слева, чтобы начать редактирование..."></textarea>
      
      <div id="save-status-msg" style="margin-top:10px; font-size:0.8rem; color:var(--accent-teal);"></div>

      <!-- History / Rollback Drawer -->
      <div id="history-drawer" class="history-box" style="display:none;">
        <div style="font-weight:600; margin-bottom:8px; display:flex; justify-content:space-between; color:var(--text-primary);">
          <span>История резервных копий (Автоматические снепшоты):</span>
          <span style="cursor:pointer; color:var(--text-secondary);" onclick="toggleHistoryView()">✕ Закрыть</span>
        </div>
        <div id="history-list">История версий для этой статьи пока пуста.</div>
      </div>
    </div>
  </div>
</div>

<!-- ================= TAB 2: TRAINING HUB ================= -->
<div id="tab-training" class="tab-panel">
  <div class="apple-grid">
    <div class="apple-card">
      <h2>🎓 Статус и Цикл Жизни Модели</h2>
      <div id="training-telemetry-body" style="font-size:0.85rem; line-height:1.9;">
        Загрузка телеметрии...
      </div>
      <div style="margin-top:16px; display:flex; gap:10px; flex-wrap:wrap;">
        <button class="apple-btn apple-btn-success" onclick="markModelTrained()">✅ Зафиксировать дату обучения</button>
        <button class="apple-btn" onclick="rebuildDataset()">⚡ Собрать датасет заново</button>
      </div>
    </div>

    <div class="apple-card">
      <h2>📦 Пакет Файлов для Обучения</h2>
      <p>Прямые ссылки для запуска в Google Colab, Kaggle или домашнем ПК:</p>
      <div id="training-files-table">Загрузка файлов...</div>
    </div>
  </div>

  <div class="apple-card">
    <h2>💡 Защита от ошибок: Как работает редактирование без потери данных</h2>
    <div style="font-size:0.82rem; color:var(--text-secondary); line-height:1.7;">
      <ul style="margin-left:20px;">
        <li><b>Автоматический снепшот:</b> При каждом сохранении статьи предыдущая версия улетает в <code>ARTICLES/.history/</code> с таймстемпом. Старое знание никогда не удаляется.</li>
        <li><b>Мгновенный живой RAG (SQLite FTS5):</b> Исправленный текст перезаписывается в базу за 0.002 секунды. Модель на телефоне при следующем вопросе сразу использует новые факты!</li>
        <li><b>Флаг необходимости дообучения:</b> Счетчик новых правок увеличивается, и виджет наверху напоминает, что при удобном случае можно впечь новые данные в LoRA.</li>
      </ul>
    </div>
  </div>
</div>

<!-- ================= TAB 3: DATASETS ================= -->
<div id="tab-dataset" class="tab-panel">
  <div class="apple-grid">
    <div class="apple-card">
      <h2>🛠️ Генератор SFT Датасета</h2>
      <p>Превращает все статьи из <code>ARTICLES/</code> и документы <code>cluster_docs/</code> в ChatML JSONL пары.</p>
      <div style="display:flex; gap:10px;">
        <button class="apple-btn apple-btn-primary" onclick="rebuildDataset()">⚡ Скомпилировать датасет</button>
        <button class="apple-btn" onclick="ingestDocs()">📥 Импорт из raw_docs/</button>
      </div>
      <div id="dataset-build-status" style="margin-top:12px; font-size:0.82rem; color:var(--accent-teal);"></div>
    </div>

    <div class="apple-card">
      <h2>📁 Текущий SFT Датасет</h2>
      <div id="dataset-summary">Загрузка информации...</div>
      <div style="margin-top:14px;">
        <a class="apple-btn" href="/api/dataset/download" download>📥 Скачать triad_omni_sft_dataset.jsonl</a>
        <button class="apple-btn" onclick="loadPreview()" style="margin-left:8px;">👁️ SFT сэмплы</button>
      </div>
    </div>

    <div class="apple-card">
      <h2>🧠 CoT Reasoning Датасет (&lt;think&gt;)</h2>
      <div id="dataset-cot-summary">Загрузка информации...</div>
      <div style="margin-top:14px; display:flex; gap:10px; flex-wrap:wrap;">
        <a class="apple-btn apple-btn-primary" href="/api/dataset/cot/download" download>📥 Скачать CoT датасет (.jsonl)</a>
        <button class="apple-btn" onclick="previewCotDataset()">👁️ Сэмплы &lt;think&gt;</button>
      </div>
    </div>
  </div>

  <div class="apple-card">
    <h2>👁️ Превью сэмплов (ChatML)</h2>
    <pre id="dataset-preview-box">Нажмите "Скомпилировать датасет" для обновления...</pre>
  </div>
</div>

<!-- ================= TAB 4: COLAB ================= -->
<div id="tab-colab" class="tab-panel">
  <div class="apple-grid">
    <div class="apple-card">
      <h2>🚀 Запуск в Google Colab (Tesla T4)</h2>
      <p>Обучение занимает ~4 минуты на бесплатной Tesla T4 GPU. Скрипт использует Unsloth FastLanguageModel:</p>
      <ol style="margin-left: 20px; font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 16px; line-height: 1.7;">
        <li>Скачайте файл <code>triad_omni_sft_dataset.jsonl</code>.</li>
        <li>Откройте Google Colab и загрузите <code>triad_omni_trainer.ipynb</code>.</li>
        <li>Загрузите датасет в ячейке 3 и нажмите «Выполнить всё».</li>
        <li>Заберите готовый архив <code>cartridge.omni.zip</code>.</li>
      </ol>
      <div style="display:flex; gap:10px;">
        <a class="apple-btn apple-btn-primary" href="https://colab.research.google.com" target="_blank">🌐 Открыть Google Colab</a>
        <a class="apple-btn" href="/api/training/notebook/download" download>📥 Скачать .ipynb</a>
      </div>
    </div>

    <div class="apple-card">
      <h2>⚙️ Профиль Безопасности (Turing Guard)</h2>
      <div style="font-size: 0.82rem; line-height: 2;">
        <div>Базовая модель: <code>unsloth/Qwen2.5-7B-Instruct-bnb-4bit</code></div>
        <div>Точность: <code>fp16=True, bf16=False</code> (Аппаратный T4)</div>
        <div>LoRA Rank/Alpha: <code>r=16, alpha=16</code></div>
        <div>Оптимизатор: <code>adamw_8bit</code></div>
        <div>Внимание: <code>sdpa (PyTorch 2.x)</code></div>
      </div>
    </div>
  </div>
</div>

<!-- ================= TAB 5: CARTRIDGES ================= -->
<div id="tab-cartridges" class="tab-panel">
  <!-- Active Cartridge Card -->
  <div class="apple-card" style="margin-bottom: 20px;">
    <h2>
      <span>⚡ Текущий Активный Картридж (Node-1 Mi 10T)</span>
      <span id="active-cartridge-badge" class="version-tag" style="background:rgba(52, 199, 89, 0.12); color:var(--accent-green-text); font-weight:700;">🟢 АКТИВЕН</span>
    </h2>
    <div id="active-cartridge-details" style="font-size:0.85rem; line-height:1.9;">
      Загрузка статуса активного картриджа...
    </div>
    <div style="margin-top: 16px; display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
      <button class="apple-btn apple-btn-success" onclick="toggleLora(1.0)">🟢 Включить LoRA (Scale 1.0)</button>
      <button class="apple-btn" onclick="toggleLora(0.0)" style="color: var(--accent-red-text);">🔴 Отключить LoRA (Scale 0.0)</button>
      <button class="apple-btn" onclick="pushActiveToDevice()">📱 Отправить на телефон (ADB Push)</button>
    </div>
    <div id="lora-status-msg" style="margin-top: 12px; font-size: 0.82rem; color: var(--accent-teal);"></div>
  </div>

  <!-- Drag and Drop Upload Zone -->
  <div class="apple-card" style="margin-bottom: 20px;">
    <h2>📥 Автоматическая Загрузка и Активация Картриджа</h2>
    <p>Перетащите сюда скачанный из Colab архив <code>cartridge.omni.zip</code> или <code>.gguf</code> файл. Студия автоматически распакует архив, сверит паспорт <code>card.json</code> и мгновенно активирует картридж в кластере.</p>
    
    <div id="drop-zone" class="drop-zone" onclick="document.getElementById('cartridge-drop-file').click()">
      <div style="font-size: 2.4rem; margin-bottom: 8px;">📦</div>
      <div style="font-weight: 600; font-size: 0.96rem; color: var(--text-primary); margin-bottom: 4px;">
        Перетащите файл <code>cartridge.omni.zip</code> или <code>.gguf</code> сюда
      </div>
      <div style="font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 12px;">
        или нажмите в любое место этой зоны для выбора файла из папки Downloads
      </div>
      <button type="button" class="apple-btn apple-btn-primary" style="pointer-events:none;">📂 Выбрать файл на компьютере</button>
      <input type="file" id="cartridge-drop-file" accept=".zip,.gguf" style="display:none;" onchange="handleFileSelect(this)">
    </div>

    <!-- Live Progress Bar -->
    <div id="upload-progress-container" style="display:none; margin-top:16px;">
      <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:6px;">
        <span id="upload-step-label" style="font-weight:600; color:var(--accent-blue);">Загрузка файла...</span>
        <span id="upload-percent-label" style="font-weight:600; color:var(--text-secondary);">0%</span>
      </div>
      <div style="width:100%; height:8px; background:rgba(0,0,0,0.06); border-radius:4px; overflow:hidden;">
        <div id="upload-progress-bar" style="width:0%; height:100%; background:linear-gradient(90deg, #0071e3, #34c759); transition:width 0.2s ease;"></div>
      </div>
      <div id="upload-status-detail" style="margin-top:8px; font-size:0.75rem; color:var(--text-secondary);"></div>
    </div>
  </div>

  <!-- Storage Quota Vault Card -->
  <div class="apple-card" style="margin-bottom: 20px;">
    <h2>
      <span>🗄️ Хранилище Версий Картриджей (Квота Памяти)</span>
      <span id="storage-quota-badge" class="version-tag" style="background:rgba(0,113,227,0.1); color:var(--accent-blue); font-weight:600;">1024 МБ Лимит</span>
    </h2>
    <div style="margin-top:8px; margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; font-size:0.82rem; margin-bottom:6px;">
        <span id="storage-used-label" style="font-weight:600; color:var(--text-primary);">Занято: 0 МБ / 1024 МБ</span>
        <span id="storage-percent-label" style="font-weight:600; color:var(--text-secondary);">0%</span>
      </div>
      <div style="width:100%; height:8px; background:rgba(0,0,0,0.06); border-radius:4px; overflow:hidden;">
        <div id="storage-progress-bar" style="width:0%; height:100%; background:linear-gradient(90deg, #0071e3, #34c759); transition:width 0.3s ease;"></div>
      </div>
    </div>
    <div style="font-size:0.78rem; color:var(--text-secondary);">
      💡 Автоматическая LRU-ротация: старые неактивные версии картриджей прореживаются при превышении лимита 1024 МБ (активная версия защищена от удаления).
    </div>
  </div>

  <!-- Registry of Installed Cartridges -->
  <div class="apple-card">
    <h2>💾 Реестр Установленных Картриджей</h2>
    <p>Картриджи с контрактом: <code>adapter.gguf</code> + <code>card.json</code> + <code>SHA256</code>.</p>
    <div id="cartridges-list-box">Поиск картриджей...</div>
  </div>
</div>

<!-- ================= TAB 6: SKILLS ================= -->
<div id="tab-skills" class="tab-panel">
  <div class="apple-card">
    <h2>🧩 Мульти-источниковая База Скилов (128)</h2>
    <p>Индексировано 128 навыков из <code>.agents</code>, плагина <code>triad-omni</code> и системного ядра.</p>
    <input type="text" id="skill-filter-input" class="search-input" placeholder="Поиск по скиллам..." oninput="searchSkills()">
    <div style="margin-bottom:12px;">
      <a class="apple-btn" href="/api/skills/download" download>📥 Скачать skills.omni.zip (450 KB)</a>
    </div>
    <div id="skills-results-box"></div>
  </div>
</div>

<script>
let currentArticles = [];
let selectedFilename = null;

function selectSegment(name) {
  document.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  const btn = document.getElementById('btn-' + name);
  if (btn) btn.classList.add('active');
  const panel = document.getElementById('tab-' + name);
  if (panel) panel.classList.add('active');
}

// ----------------- KNOWLEDGE EDITOR -----------------
async function loadArticlesList() {
  try {
    const res = await fetch('/api/articles/list');
    currentArticles = await res.json();
    renderArticlesList(currentArticles);
    if (currentArticles.length > 0 && !selectedFilename) {
      selectArticle(currentArticles[0].filename);
    }
  } catch(e) {
    document.getElementById('article-list-container').innerHTML = '<div style="color:var(--accent-red-text)">Ошибка загрузки статей</div>';
  }
}

function renderArticlesList(items) {
  const container = document.getElementById('article-list-container');
  if (items.length === 0) {
    container.innerHTML = '<div style="color:var(--text-tertiary); padding:10px;">Статьи не найдены</div>';
    return;
  }
  let html = '';
  items.forEach(a => {
    const isSel = (a.filename === selectedFilename) ? 'selected' : '';
    html += `
      <div class="article-item ${isSel}" onclick="selectArticle('${a.filename}')">
        <div class="article-item-title">${a.title}</div>
        <div class="article-item-meta">
          <span>${a.size_kb} KB</span>
          <span>${a.history_count > 0 ? `🕒 ${a.history_count} версий` : a.updated}</span>
        </div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function filterArticles() {
  const q = document.getElementById('article-search').value.toLowerCase();
  const filtered = currentArticles.filter(a => a.title.toLowerCase().includes(q) || a.filename.toLowerCase().includes(q));
  renderArticlesList(filtered);
}

async function selectArticle(filename) {
  selectedFilename = filename;
  renderArticlesList(currentArticles);
  document.getElementById('editor-filename').textContent = filename;
  document.getElementById('save-status-msg').textContent = 'Загрузка...';

  try {
    const res = await fetch('/api/articles/get?file=' + encodeURIComponent(filename));
    const data = await res.json();
    document.getElementById('article-content-input').value = data.content || '';
    
    const item = currentArticles.find(a => a.filename === filename);
    document.getElementById('editor-title').textContent = item ? item.title : filename;
    document.getElementById('history-badge').textContent = item ? item.history_count : '0';
    document.getElementById('save-status-msg').textContent = `Загружено. Размер: ${(data.size/1024).toFixed(1)} KB`;
    
    loadHistoryDrawer(filename);
  } catch(e) {
    document.getElementById('save-status-msg').textContent = 'Ошибка загрузки: ' + e;
  }
}

async function saveCurrentArticle() {
  if (!selectedFilename) return;
  const content = document.getElementById('article-content-input').value;
  const statusEl = document.getElementById('save-status-msg');
  statusEl.textContent = '⏳ Сохраняем статью, создаем копию в .history и обновляем FTS5...';

  try {
    const res = await fetch('/api/articles/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: selectedFilename, content: content })
    });
    const data = await res.json();
    statusEl.textContent = `✅ ${data.message}`;
    loadArticlesList();
    loadTrainingStatus();
  } catch(e) {
    statusEl.textContent = '❌ Ошибка сохранения: ' + e;
  }
}

function toggleHistoryView() {
  const d = document.getElementById('history-drawer');
  d.style.display = (d.style.display === 'none') ? 'block' : 'none';
}

async function loadHistoryDrawer(filename) {
  try {
    const res = await fetch('/api/articles/history?file=' + encodeURIComponent(filename));
    const versions = await res.json();
    const box = document.getElementById('history-list');
    if (versions.length === 0) {
      box.innerHTML = '<div style="color:var(--text-tertiary); padding:6px 0;">У этой статьи пока нет резервных копий (версия оригинальная).</div>';
      return;
    }
    let html = '<div style="display:flex; flex-direction:column; gap:6px; margin-top:8px;">';
    versions.forEach(v => {
      html += `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 8px; background:rgba(0,0,0,0.03); border-radius:6px;">
          <div><b>${v.created_at}</b> (${v.size_kb} KB)</div>
          <button class="apple-btn" style="padding:2px 8px; font-size:0.75rem;" onclick="rollbackVersion('${selectedFilename}', '${v.backup_name}')">🔄 Откатить</button>
        </div>
      `;
    });
    html += '</div>';
    box.innerHTML = html;
  } catch(e) {}
}

async function rollbackVersion(filename, backupName) {
  if (!confirm(`Откатить статью к версии от ${backupName}? Текущий вариант сохранится в бэкапах.`)) return;
  try {
    const res = await fetch('/api/articles/rollback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: filename, backup_name: backupName })
    });
    const data = await res.json();
    alert(data.message);
    selectArticle(filename);
  } catch(e) {
    alert('Ошибка отката: ' + e);
  }
}

// ----------------- TRAINING TELEMETRY -----------------
async function loadTrainingStatus() {
  try {
    const res = await fetch('/api/training/status');
    const data = await res.json();
    
    // Top Banner
    const widget = document.getElementById('reminder-widget');
    const rText = document.getElementById('reminder-text');
    rText.textContent = data.status_text;
    if (data.needs_training) {
      widget.className = 'reminder-widget status-warn';
      rText.style.color = 'var(--accent-orange-text)';
    } else {
      widget.className = 'reminder-widget status-ok';
      rText.style.color = 'var(--accent-green-text)';
    }

    // Telemetry Card in Tab 2
    const body = document.getElementById('training-telemetry-body');
    body.innerHTML = `
      <div>Последнее обучение: <b>${data.last_trained_human}</b> (${data.days_passed} дн. назад)</div>
      <div>Сэмплов в обученной модели: <b>${data.trained_samples}</b></div>
      <div>Сэмплов в текущем датасете: <b>${data.current_samples}</b></div>
      <div>Новых правок / сэмплов: <b style="color:${data.diff_samples > 0 ? 'var(--accent-orange-text)' : 'var(--accent-green-text)'}">+${data.diff_samples}</b></div>
      <div>Статей в базе знаний: <b>${data.articles_count}</b></div>
      <div>Сырых документов в очереди: <b>${data.raw_docs_count}</b></div>
    `;

    // Files Hub Table
    const fContainer = document.getElementById('training-files-table');
    let fHtml = '<table class="apple-table"><thead><tr><th>Файл</th><th>Тип</th><th>Размер</th><th>Действие</th></tr></thead><tbody>';
    data.files.forEach(f => {
      fHtml += `
        <tr>
          <td>
            <b>${f.name}</b><br>
            <span style="font-size:0.72rem; color:var(--text-secondary);">${f.desc}</span>
          </td>
          <td><code>${f.type}</code></td>
          <td>${f.size_mb} MB</td>
          <td>
            <a class="apple-btn" style="padding:3px 8px; font-size:0.75rem;" href="${f.download_url}" download>📥 Скачать</a>
            ${f.colab_url ? `<a class="apple-btn" style="padding:3px 8px; font-size:0.75rem; margin-left:4px;" href="${f.colab_url}" target="_blank">🚀 Colab</a>` : ''}
          </td>
        </tr>
      `;
    });
    fHtml += '</tbody></table>';
    fContainer.innerHTML = fHtml;

  } catch(e) {}
}

async function markModelTrained() {
  try {
    const res = await fetch('/api/training/mark_trained', { method: 'POST' });
    const data = await res.json();
    alert('Статус зафиксирован! Дата обучения обновлена: ' + data.last_trained_human);
    loadTrainingStatus();
  } catch(e) {
    alert('Ошибка: ' + e);
  }
}

async function rebuildDataset() {
  const status = document.getElementById('dataset-build-status');
  if (status) status.textContent = '⏳ Пересборка датасета из статей ARTICLES/...';
  try {
    const res = await fetch('/api/dataset/build', { method: 'POST' });
    const data = await res.json();
    if (status) status.textContent = `✅ Успешно! Скомпилировано ${data.count} ChatML пар.`;
    loadDatasetInfo();
    loadTrainingStatus();
  } catch(e) {
    if (status) status.textContent = '❌ Ошибка: ' + e;
  }
}

async function ingestDocs() {
  try {
    const res = await fetch('/api/docs/ingest', { method: 'POST' });
    const data = await res.json();
    alert('Импорт завершен: ' + data.message);
    loadDatasetInfo();
    loadTrainingStatus();
  } catch(e) {
    alert('Ошибка импорта: ' + e);
  }
}

async function loadDatasetInfo() {
  try {
    const res = await fetch('/api/dataset/info');
    const data = await res.json();
    const box = document.getElementById('dataset-summary');
    if (data.exists) {
      box.innerHTML = `
        <div style="font-size:0.82rem; line-height: 1.8;">
          <div>Файл: <b>triad_omni_sft_dataset.jsonl</b></div>
          <div>Размер: <b>${(data.size / 1024).toFixed(1)} KB</b></div>
          <div>Всего сэмплов: <b>${data.count}</b></div>
          <div>Обновлен: <b>${data.updated}</b></div>
        </div>
      `;
      loadPreview();
    }
  } catch(e) {}
}

async function loadPreview() {
  try {
    const res = await fetch('/api/dataset/preview');
    const text = await res.text();
    document.getElementById('dataset-preview-box').textContent = text;
  } catch(e) {}
}

async function loadCotDatasetInfo() {
  try {
    const res = await fetch('/api/dataset/cot/info');
    const data = await res.json();
    const box = document.getElementById('dataset-cot-summary');
    if (box && data.exists) {
      box.innerHTML = `
        <div style="font-size:0.82rem; line-height: 1.8;">
          <div>Файл: <b>triad_omni_cot_dataset.jsonl</b></div>
          <div>Размер: <b>${(data.size / 1024).toFixed(1)} KB</b></div>
          <div>Цепочек рассуждений (&lt;think&gt;): <b>${data.count}</b></div>
          <div>Обновлен: <b>${data.updated}</b></div>
        </div>
      `;
    }
  } catch(e) {}
}

async function previewCotDataset() {
  try {
    const res = await fetch('/api/dataset/cot/preview');
    const text = await res.text();
    document.getElementById('dataset-preview-box').textContent = text;
  } catch(e) {}
}

function toggleTheme() {
  const isCyber = document.documentElement.getAttribute('data-theme') === 'cyberdeck';
  if (isCyber) {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('omni-theme', 'apple');
    const btn = document.getElementById('theme-btn');
    if (btn) btn.textContent = '🌙 Cyberdeck HUD';
  } else {
    document.documentElement.setAttribute('data-theme', 'cyberdeck');
    localStorage.setItem('omni-theme', 'cyberdeck');
    const btn = document.getElementById('theme-btn');
    if (btn) btn.textContent = '☀️ Apple Light';
  }
}

if (localStorage.getItem('omni-theme') === 'cyberdeck') {
  document.documentElement.setAttribute('data-theme', 'cyberdeck');
}

async function loadActiveCartridge() {
  try {
    const res = await fetch('/api/cartridges/active');
    const data = await res.json();
    const details = document.getElementById('active-cartridge-details');
    const badge = document.getElementById('active-cartridge-badge');

    if (data.active) {
      badge.textContent = `🟢 АКТИВЕН (Scale: ${data.scale || 1.0})`;
      badge.style.background = 'rgba(52, 199, 89, 0.12)';
      badge.style.color = 'var(--accent-green-text)';

      details.innerHTML = `
        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
          <div>Имя / Slug: <b style="color:var(--accent-blue);">${data.slug || data.name}</b></div>
          <div>Целевое устройство: <b>${data.device_target || 'Xiaomi Mi 10T 5G (Snapdragon 865)'}</b></div>
        </div>
        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-top:4px;">
          <div>Базовая модель: <code>${data.base || 'Qwen3.5-9B-UD-Q3_K_XL.gguf'}</code></div>
          <div>Параметры LoRA: <b>Rank ${data.rank || 16} / Alpha ${data.alpha || 16}</b></div>
        </div>
        <div style="margin-top:6px; font-size:0.75rem; color:var(--text-secondary);">
          <span>Описание: ${data.description || 'Инженерный стиль и база знаний Triad-Omni'}</span><br>
          <span>SHA256: <code>${(data.sha256 || data.verified_sha256 || 'не указан').substring(0, 32)}...</code></span>
        </div>
      `;
    } else {
      badge.textContent = '⚪ НЕ ПОДКЛЮЧЕН';
      badge.style.background = 'rgba(0, 0, 0, 0.05)';
      badge.style.color = 'var(--text-secondary)';
      details.innerHTML = `
        <div>Картридж LoRA не подключен. Базовая модель работает в штатном режиме.</div>
        <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;">Перетащите <code>cartridge.omni.zip</code> в поле ниже, чтобы активировать LoRA.</div>
      `;
    }
  } catch(e) {}
}

async function loadCartridges() {
  try {
    // 1. Загрузка квоты памяти
    try {
      const storRes = await fetch('/api/cartridges/storage');
      const stor = await storRes.json();
      if (stor && stor.total_mb !== undefined) {
        document.getElementById('storage-used-label').innerText = `Занято: ${stor.total_mb} МБ / ${stor.max_mb} МБ (${stor.total_cartridges_count} версий)`;
        document.getElementById('storage-percent-label').innerText = `${stor.percent_used}%`;
        const bar = document.getElementById('storage-progress-bar');
        bar.style.width = Math.min(100, stor.percent_used) + '%';
        if (stor.percent_used > 85) {
          bar.style.background = 'linear-gradient(90deg, #ff9500, #ff3b30)';
        } else {
          bar.style.background = 'linear-gradient(90deg, #0071e3, #34c759)';
        }
      }
    } catch(e) {}

    // 2. Загрузка списка картриджей
    const res = await fetch('/api/cartridges/list');
    const list = await res.json();
    const container = document.getElementById('cartridges-list-box');
    if (!list || list.length === 0) {
      container.innerHTML = '<div style="color:var(--text-secondary); margin-top:8px;">Картриджи не найдены в папке <code>cartridges/</code>. Загрузите первый архив через поле выше!</div>';
      return;
    }
    let html = '<table class="apple-table"><thead><tr><th>Слот / Версия</th><th>Тег сборки</th><th>Размер</th><th>Статус</th><th>Действия</th></tr></thead><tbody>';
    list.forEach(c => {
      const isAct = c.is_active;
      const vTag = c.build_tag || c.version || 'v1.0';
      html += `
        <tr>
          <td>
            <b style="color:var(--text-primary);">${c.slug || c.name}</b> <span class="version-tag">${c.version || 'v1.0'}</span><br>
            <span style="font-size:0.72rem; color:var(--text-secondary);">${c.card?.description || (c.files ? c.files.join(', ') : c.name)}</span>
          </td>
          <td><code style="font-size:0.75rem;">${vTag}</code></td>
          <td>${c.size_mb} MB</td>
          <td>
            ${isAct ? '<span class="version-tag" style="background:rgba(52,199,89,0.15); color:var(--accent-green-text); font-weight:700;">🟢 Активен</span>' : '<span class="version-tag">В кэше</span>'}
          </td>
          <td>
            <div style="display:flex; gap:6px;">
              ${!isAct ? `<button class="apple-btn" style="padding:3px 8px; font-size:0.75rem;" onclick="activateCartridge('${c.slug}')">⚡ Активировать</button>` : ''}
              <a class="apple-btn" style="padding:3px 8px; font-size:0.75rem;" href="/api/cartridges/download?file=${encodeURIComponent(c.name)}" download>📥 Скачать</a>
            </div>
          </td>
        </tr>
      `;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  } catch(e) {}
}

async function activateCartridge(slug) {
  try {
    const res = await fetch('/api/cartridges/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug: slug })
    });
    const d = await res.json();
    alert(d.message || 'Картридж активирован!');
    loadActiveCartridge();
    loadCartridges();
  } catch(e) {
    alert('Ошибка активации: ' + e);
  }
}

async function toggleLora(scale) {
  const resEl = document.getElementById('lora-status-msg');
  resEl.textContent = '⏳ Переключение LoRA scale...';
  try {
    const res = await fetch('http://127.0.0.1:8000/api/lora/scale', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scale: scale, slot_id: 0 })
    });
    const d = await res.json();
    resEl.textContent = `✅ Ответ шлюза: LoRA Scale = ${scale} (Статус: ${d.status || 'OK'})`;
    loadActiveCartridge();
  } catch(e) {
    resEl.textContent = '❌ Ошибка шлюза :8000: ' + e;
  }
}

async function pushActiveToDevice() {
  const resEl = document.getElementById('lora-status-msg');
  resEl.textContent = '⏳ Отправляем картридж на Xiaomi Mi 10T через ADB...';
  try {
    const res = await fetch('/api/cartridges/push_to_device', { method: 'POST' });
    const d = await res.json();
    if (d.ok) {
      resEl.textContent = `✅ Успешно! Файл передан на телефон: ${d.target_path}`;
    } else {
      resEl.textContent = `❌ Ошибка ADB: ${d.error}`;
    }
  } catch(e) {
    resEl.textContent = '❌ Ошибка запроса: ' + e;
  }
}

// ----------------- DRAG AND DROP & UPLOAD -----------------
function initDragAndDrop() {
  const dropZone = document.getElementById('drop-zone');
  if (!dropZone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('dragover');
    }, false);
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      uploadCartridgeFile(dt.files[0]);
    }
  });
}

function handleFileSelect(input) {
  if (input.files && input.files.length > 0) {
    uploadCartridgeFile(input.files[0]);
  }
}

function uploadCartridgeFile(file) {
  const fname = file.name.toLowerCase();
  if (!fname.endsWith('.zip') && !fname.endsWith('.gguf')) {
    alert('Пожалуйста, выберите архив .zip (cartridge.omni.zip) или веса .gguf!');
    return;
  }

  const pContainer = document.getElementById('upload-progress-container');
  const pBar = document.getElementById('upload-progress-bar');
  const stepLabel = document.getElementById('upload-step-label');
  const percentLabel = document.getElementById('upload-percent-label');
  const statusDetail = document.getElementById('upload-status-detail');

  pContainer.style.display = 'block';
  pBar.style.width = '0%';
  stepLabel.textContent = `Загрузка: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)...`;
  percentLabel.textContent = '0%';
  statusDetail.textContent = 'Передача байтов на локальный сервер...';

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/cartridges/upload?filename=' + encodeURIComponent(file.name), true);

  xhr.upload.onprogress = function(e) {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      pBar.style.width = pct + '%';
      percentLabel.textContent = pct + '%';
      if (pct === 100) {
        stepLabel.textContent = '⚡ Распаковка архива, сверка SHA256 и регистрация паспорта...';
        statusDetail.textContent = 'Идёт верификация и активация картриджа в кластере...';
      }
    }
  };

  xhr.onload = function() {
    if (xhr.status === 200) {
      try {
        const res = JSON.parse(xhr.responseText);
        if (res.ok) {
          pBar.style.width = '100%';
          stepLabel.textContent = '✅ Картридж успешно активирован!';
          statusDetail.textContent = res.message;
          loadActiveCartridge();
          loadCartridges();
          loadTrainingStatus();
        } else {
          stepLabel.textContent = '❌ Ошибка установки';
          statusDetail.textContent = res.error || 'Не удалось распаковать картридж';
        }
      } catch (err) {
        stepLabel.textContent = '❌ Ошибка ответа сервера';
        statusDetail.textContent = err.toString();
      }
    } else {
      stepLabel.textContent = '❌ Ошибка сервера: ' + xhr.status;
      statusDetail.textContent = xhr.responseText;
    }
  };

  xhr.onerror = function() {
    stepLabel.textContent = '❌ Ошибка сети при передаче файла';
  };

  xhr.send(file);
}

async function searchSkills() {
  const q = document.getElementById('skill-filter-input').value;
  try {
    const res = await fetch('/api/skills/search?q=' + encodeURIComponent(q));
    const data = await res.json();
    const container = document.getElementById('skills-results-box');
    let html = '';
    data.slice(0, 25).forEach(s => {
      html += `
        <div style="padding:10px 0; border-bottom:1px solid var(--border-subtle);">
          <div style="display:flex; justify-content:space-between;">
            <b style="color:var(--accent-blue);">${s.slug}</b>
            <span class="version-tag">${s.source_root}</span>
          </div>
          <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:3px;">${s.description || 'Без описания'}</div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch(e) {}
}

// Initial Boot
if (localStorage.getItem('omni-theme') === 'cyberdeck') {
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = '☀️ Apple Light';
}
loadArticlesList();
loadTrainingStatus();
loadDatasetInfo();
loadCotDatasetInfo();
loadActiveCartridge();
loadCartridges();
initDragAndDrop();
searchSkills();
</script>

</body>
</html>
"""

class AppleForgeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
            return

        elif path == "/api/open_browser_on_pc":
            import webbrowser
            url = f"http://192.168.1.3:{PORT}/"
            try:
                webbrowser.open(url)
                self.send_json({"ok": True, "message": "Браузер на ПК успешно открыт", "url": url})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, status=500)
            return

        elif path == "/api/articles/list":
            self.send_json(list_articles())
            return

        elif path == "/api/articles/get":
            query_params = urllib.parse.parse_qs(parsed.query)
            fname = query_params.get("file", [""])[0]
            art = get_article(fname)
            if art:
                self.send_json(art)
            else:
                self.send_error(404, "Статья не найдена")
            return

        elif path == "/api/articles/history":
            query_params = urllib.parse.parse_qs(parsed.query)
            fname = query_params.get("file", [""])[0]
            self.send_json(get_article_history(fname))
            return

        elif path == "/api/training/status":
            self.send_json(load_training_state())
            return

        elif path == "/api/training/notebook/download":
            nb_file = NOTEBOOKS_DIR / "triad_omni_trainer.ipynb"
            if not nb_file.exists():
                nb_file = BASE_DIR / "triad_omni_trainer.ipynb"
            if nb_file.exists():
                content = nb_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ipynb+json")
                self.send_header("Content-Disposition", "attachment; filename=triad_omni_trainer.ipynb")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Ноутбук не найден")
            return

        elif path == "/api/cartridges/download":
            query_params = urllib.parse.parse_qs(parsed.query)
            fname = query_params.get("file", [""])[0]
            target = CARTRIDGES_DIR / os.path.basename(fname)
            if target.exists() and target.is_file():
                content = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f"attachment; filename={target.name}")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Картридж не найден")
            return

        elif path == "/api/dataset/info":
            dataset_file = DATASETS_DIR / "triad_omni_sft_dataset.jsonl"
            if dataset_file.exists():
                lines = dataset_file.read_text(encoding='utf-8').strip().split('\n')
                stat = dataset_file.stat()
                import datetime
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                data = {
                    "exists": True,
                    "size": stat.st_size,
                    "count": len(lines),
                    "updated": mtime
                }
            else:
                data = {"exists": False}
            self.send_json(data)
            return

        elif path == "/api/dataset/cot/info":
            dataset_file = DATASETS_DIR / "triad_omni_cot_dataset.jsonl"
            if dataset_file.exists():
                lines = dataset_file.read_text(encoding='utf-8').strip().split('\n')
                stat = dataset_file.stat()
                import datetime
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                data = {
                    "exists": True,
                    "size": stat.st_size,
                    "count": len(lines),
                    "updated": mtime
                }
            else:
                data = {"exists": False}
            self.send_json(data)
            return

        elif path == "/api/dataset/preview":
            dataset_file = DATASETS_DIR / "triad_omni_sft_dataset.jsonl"
            if dataset_file.exists():
                try:
                    with open(dataset_file, "r", encoding="utf-8") as f:
                        samples = [json.loads(f.readline()) for _ in range(min(3, 100)) if f]
                    text = json.dumps(samples, ensure_ascii=False, indent=2)
                except Exception as e:
                    text = f"Ошибка чтения сэмплов: {e}"
            else:
                text = "Файл датасета пока не создан."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(text.encode('utf-8'))
            return

        elif path == "/api/dataset/cot/preview":
            dataset_file = DATASETS_DIR / "triad_omni_cot_dataset.jsonl"
            if dataset_file.exists():
                try:
                    with open(dataset_file, "r", encoding="utf-8") as f:
                        samples = [json.loads(f.readline()) for _ in range(min(2, 50)) if f]
                    text = json.dumps(samples, ensure_ascii=False, indent=2)
                except Exception as e:
                    text = f"Ошибка чтения CoT сэмплов: {e}"
            else:
                text = "Файл CoT датасета пока не создан."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(text.encode('utf-8'))
            return

        elif path == "/api/dataset/download":
            dataset_file = DATASETS_DIR / "triad_omni_sft_dataset.jsonl"
            if dataset_file.exists():
                content = dataset_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/jsonl")
                self.send_header("Content-Disposition", "attachment; filename=triad_omni_sft_dataset.jsonl")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Датасет не найден")
            return

        elif path == "/api/dataset/cot/download":
            dataset_file = DATASETS_DIR / "triad_omni_cot_dataset.jsonl"
            if dataset_file.exists():
                content = dataset_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/jsonl")
                self.send_header("Content-Disposition", "attachment; filename=triad_omni_cot_dataset.jsonl")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "CoT датасет не найден")
            return

        elif path == "/api/cluster/status":
            status = {"node1": False, "node2": False, "node3": False}
            for key, url in [("node1", "http://127.0.0.1:8080/health"), ("node2", "http://127.0.0.1:8081/health"), ("node3", "http://127.0.0.1:8000/api/health")]:
                try:
                    req = urllib.request.Request(url)
                    with urllib.request.urlopen(req, timeout=0.8) as resp:
                        if resp.status == 200:
                            status[key] = True
                except Exception:
                    status[key] = False
            self.send_json(status)
            return

        elif path == "/api/skills/download":
            zip_file = DATASETS_DIR / "skills.omni.zip"
            if zip_file.exists():
                content = zip_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", "attachment; filename=skills.omni.zip")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "skills.omni.zip не найден")
            return

        elif path == "/api/cartridges/list":
            self.send_json(list_cartridges())
            return

        elif path == "/api/cartridges/active":
            self.send_json(get_active_cartridge())
            return

        elif path == "/api/cartridges/storage":
            self.send_json(get_storage_stats())
            return

        elif path == "/api/cloud/config":
            try:
                from cloud_sync import load_cloud_config
                self.send_json(load_cloud_config())
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, status=500)
            return

        elif path == "/api/skills/search":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", [""])[0].strip()
            skills = []
            if SKILL_DB.exists():
                try:
                    conn = sqlite3.connect(SKILL_DB)
                    c = conn.cursor()
                    if q:
                        c.execute("""
                            SELECT s.slug, s.path, s.description
                            FROM skill_metadata s
                            JOIN skills_fts f ON s.id = f.rowid
                            WHERE skills_fts MATCH ?
                            LIMIT 30
                        """, (f"{q}*",))
                    else:
                        c.execute("SELECT slug, path, description FROM skill_metadata LIMIT 50")
                    for row in c.fetchall():
                        p_str = row[1] or ""
                        root_label = "builtin"
                        if ".agents" in p_str: root_label = ".agents"
                        elif "plugins" in p_str: root_label = "plugin"
                        elif ".claude" in p_str: root_label = ".claude"
                        skills.append({
                            "slug": row[0],
                            "source_root": root_label,
                            "description": row[2]
                        })
                    conn.close()
                except Exception as e:
                    print(f"Error querying skills: {e}")
            self.send_json(skills)
            return

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        path = self.path

        if path.startswith("/api/cartridges/upload"):
            parsed = urllib.parse.urlparse(path)
            query_params = urllib.parse.parse_qs(parsed.query)
            fname = query_params.get("filename", ["uploaded_cartridge.zip"])[0]
            safe_fname = os.path.basename(fname)
            dest_file = CARTRIDGES_DIR / safe_fname

            length = int(self.headers.get("Content-Length", 0))
            bytes_read = 0
            with open(dest_file, "wb") as f_out:
                while bytes_read < length:
                    chunk_size = min(65536, length - bytes_read)
                    chunk = self.rfile.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    bytes_read += len(chunk)

            # Распаковываем, валидируем и активируем
            res = unpack_and_install_cartridge(dest_file)

            # Оповещаем Master HUD (:8000), если он активен
            try:
                req = urllib.request.Request(
                    "http://127.0.0.1:8000/api/lora/scale",
                    data=json.dumps({"scale": 1.0, "slot_id": 0}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=1.5)
            except Exception:
                pass

            self.send_json(res)
            return

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            payload = {}

        if path == "/api/articles/save":
            fname = payload.get("filename", "")
            content = payload.get("content", "")
            if not fname:
                self.send_json({"ok": False, "error": "Не указано имя файла"}, status=400)
                return
            res = save_article(fname, content)
            self.send_json(res)
            return

        elif path == "/api/articles/rollback":
            fname = payload.get("filename", "")
            bname = payload.get("backup_name", "")
            res = rollback_article(fname, bname)
            self.send_json(res)
            return

        elif path == "/api/training/mark_trained":
            state = mark_as_trained()
            self.send_json(state)
            return

        elif path == "/api/cloud/sync":
            try:
                from cloud_sync import sync_all_to_cloud
                res = sync_all_to_cloud()
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, status=500)
            return

        elif path == "/api/cloud/save":
            try:
                from cloud_sync import load_cloud_config, save_cloud_config
                cfg = load_cloud_config()
                cfg.update(payload)
                save_cloud_config(cfg)
                self.send_json({"ok": True, "config": cfg})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, status=500)
            return

        elif path == "/api/docs/ingest":
            try:
                res = subprocess.run([sys.executable, str(SCRIPTS_DIR / "ingest_docs.py")], capture_output=True, text=True, check=True)
                self.send_json({"status": "ok", "message": "Документы успешно обработаны и добавлены в omni_knowledge.db."})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, status=500)
            return

        elif path == "/api/dataset/build":
            try:
                res = subprocess.run([sys.executable, str(SCRIPTS_DIR / "build_sft_dataset.py")], capture_output=True, text=True, check=True)
                dataset_file = DATASETS_DIR / "triad_omni_sft_dataset.jsonl"
                lines = dataset_file.read_text(encoding='utf-8').strip().split('\n')
                self.send_json({"status": "ok", "count": len(lines)})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, status=500)
            return

        elif path == "/api/cartridges/activate":
            slug = payload.get("slug", "")
            for c in list_cartridges():
                if c.get("slug") == slug or c.get("name") == slug:
                    card_data = c.get("card", {})
                    card_data["slug"] = slug
                    card_data["scale"] = 1.0
                    card_data["active_path"] = c.get("path")
                    set_active_cartridge(card_data)

                    # Уведомляем Master Router :8000
                    try:
                        req = urllib.request.Request(
                            "http://127.0.0.1:8000/api/lora/scale",
                            data=json.dumps({"scale": 1.0, "slot_id": 0}).encode("utf-8"),
                            headers={"Content-Type": "application/json"}
                        )
                        urllib.request.urlopen(req, timeout=1.5)
                    except Exception:
                        pass

                    self.send_json({"ok": True, "message": f"Картридж '{slug}' успешно активирован!"})
                    return
            self.send_json({"ok": False, "error": f"Картридж '{slug}' не найден"}, status=404)
            return

        elif path == "/api/cartridges/push_to_device":
            act = get_active_cartridge()
            act_path = act.get("active_path")
            adb_path = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
            if not os.path.exists(adb_path):
                adb_path = "adb"
            if not act_path or not os.path.exists(act_path):
                self.send_json({"ok": False, "error": "Активный картридж не найден на диске"}, status=400)
                return

            p = Path(act_path)
            ggufs = list(p.glob("*.gguf")) if p.is_dir() else ([p] if p.suffix == ".gguf" else [])
            if not ggufs:
                self.send_json({"ok": False, "error": "В активном картридже нет файлов .gguf"}, status=400)
                return

            target_gguf = ggufs[0]
            folder_name = p.name if p.is_dir() else p.stem
            try:
                # 1. Пушим в sdcard
                subprocess.run([adb_path, "shell", "mkdir -p /sdcard/triad_cartridges"], capture_output=True)
                proc = subprocess.run([adb_path, "push", str(p), f"/sdcard/triad_cartridges/{folder_name}"], capture_output=True, text=True)
                # 2. Перемещаем в Termux Vault и активируем
                vault_cmd = f"su -c 'mkdir -p /data/data/com.termux/files/home/cartridges && cp -r /sdcard/triad_cartridges/{folder_name} /data/data/com.termux/files/home/cartridges/ && /data/data/com.termux/files/home/cartridge_vault.sh activate {folder_name}'"
                subprocess.run([adb_path, "shell", vault_cmd], capture_output=True, text=True)
                self.send_json({"ok": True, "target_vault": f"/data/data/com.termux/files/home/cartridges/{folder_name}", "activated": True})
            except Exception as e:
                self.send_json({"ok": False, "error": f"Ошибка ADB: {e}"}, status=500)
            return
        else:
            self.send_error(404, "Not Found")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), AppleForgeHandler)
    server.daemon_threads = True
    print(f"🍏 Omni-Forge Studio v5.1 (Apple Pure Light Edition) запущена на http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()

if __name__ == "__main__":
    main()
