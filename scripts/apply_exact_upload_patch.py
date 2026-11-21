#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

file_path = Path("scripts/build_updated_web_ui.py")
content = file_path.read_text(encoding="utf-8")

# 1. Update HTML label and add progress bar
target_html = '''            <label class="ios-btn ios-btn-secondary" style="cursor:pointer;">
              <span>📁 Выбрать файл</span>
              <input type="file" id="local-cartridge-picker" accept=".zip,.gguf" style="display:none;" onchange="handleLocalCartridgeFile(this)">
            </label>
          </div>
        </div>'''

replace_html = '''            <label class="ios-btn ios-btn-secondary" style="cursor:pointer;">
              <span>📁 Выбрать .omni.zip</span>
              <input type="file" id="local-cartridge-picker" accept=".zip,.gguf,.omni.zip" style="display:none;" onchange="handleLocalCartridgeFile(this)">
            </label>
          </div>

          <!-- Upload progress bar container -->
          <div id="cartridge-upload-progress-box" style="display:none; margin-top:10px;">
            <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px;">
              <span id="upload-status-text" style="color:var(--apple-blue); font-weight:600;">Загрузка файла в cartridges/...</span>
              <span id="upload-percent-text" style="font-family:var(--font-mono); color:var(--text-secondary);">0%</span>
            </div>
            <div class="quota-bar-wrapper" style="height:6px;">
              <div class="quota-progress" id="cartridge-upload-bar" style="width: 0%; background:var(--apple-blue); transition: width 0.2s ease;"></div>
            </div>
          </div>
        </div>'''

if target_html in content:
    content = content.replace(target_html, replace_html, 1)
    print("✅ Replaced HTML target")
else:
    print("❌ target_html not found")

# 2. Replace handleLocalCartridgeFile JS
idx_start = content.find("  // Handle Local Cartridge File Picker\n  function handleLocalCartridgeFile(input) {")
idx_end = content.find("  // Export Knowledge Base into Fresh SFT Dataset")

new_fn = '''  // Handle Real HTTP File Upload into cartridges/
  function handleLocalCartridgeFile(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
    
    const progressBox = document.getElementById('cartridge-upload-progress-box');
    const progressBar = document.getElementById('cartridge-upload-bar');
    const statusText = document.getElementById('upload-status-text');
    const percentText = document.getElementById('upload-percent-text');
    
    if (progressBox) progressBox.style.display = 'block';
    if (progressBar) {
      progressBar.style.width = '0%';
      progressBar.style.background = 'var(--apple-blue)';
    }
    if (statusText) {
      statusText.style.color = 'var(--apple-blue)';
      statusText.innerText = `⏳ Загрузка ${file.name} (${sizeMb} МБ) в папку cartridges/...`;
    }
    
    addTerminalLog(`[Upload] Uploading ${file.name} (${sizeMb} MB) directly into cartridges/ folder...`);
    
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/cartridge/upload?filename=' + encodeURIComponent(file.name), true);
    xhr.setRequestHeader('X-Filename', encodeURIComponent(file.name));
    xhr.setRequestHeader('Content-Type', 'application/octet-stream');
    
    xhr.upload.onprogress = function(e) {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        if (progressBar) progressBar.style.width = percent + '%';
        if (percentText) percentText.innerText = percent + '%';
      }
    };
    
    xhr.onload = function() {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res = JSON.parse(xhr.responseText);
          if (progressBar) {
            progressBar.style.width = '100%';
            progressBar.style.background = 'var(--apple-green)';
          }
          if (percentText) percentText.innerText = '100%';
          if (statusText) {
            statusText.style.color = 'var(--apple-green)';
            statusText.innerText = `✅ Файл сохранен в cartridges/${res.filename} (${res.size_mb} МБ)!`;
          }
          
          const cardInfo = res.card || {};
          const desc = cardInfo.description || (cardInfo.slug ? cardInfo.slug + ' ' + (cardInfo.version || '') : '');
          
          alert(`🎉 Успех!\\n\\nАрхив ${res.filename} (${res.size_mb} МБ) успешно сохранен через веб-интерфейс прямо в папку cartridges/ проекта!\\n\\nПаспорт: ${desc || 'omni.lora.card/1'}\\n\\nФайл автоматически добавлен в список для прошивки в Xiaomi Mi 10T 5G.`);
          
          // Reload dropdowns and lists
          loadLocalCartridgesList();
          loadCartridgeVault();
          addTerminalLog(`[Upload] Finished: Saved ${res.filename} (${res.size_mb} MB) to cartridges/. Ready for flash.`);
        } catch(err) {
          alert('Файл загружен, но произошла ошибка парсинга ответа: ' + err.message);
        }
      } else {
        alert('❌ Ошибка загрузки архива: HTTP ' + xhr.status);
      }
    };
    
    xhr.onerror = function() {
      alert('❌ Сетевой сбой при передаче архива на сервер!');
    };
    
    xhr.send(file);
  }

'''

if idx_start != -1 and idx_end != -1:
    content = content[:idx_start] + new_fn + content[idx_end:]
    print("✅ Replaced handleLocalCartridgeFile JS block")
else:
    print("❌ JS target indices not found")

file_path.write_text(content, encoding="utf-8")
print("🎉 Applied exact patch!")
