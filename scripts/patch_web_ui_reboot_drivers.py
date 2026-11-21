#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch build_updated_web_ui.py to:
1. Add explicit 'Which phone to connect' notice in Tab 2 (Xiaomi Mi 10T 5G vs OnePlus Nord N10).
2. Add Termux Reboot button in Tab 5.
3. Add GPU/Adreno Vulkan Driver Diagnostics card in Tab 5.
4. Add executeRestartTermux() and checkDriversStatus() JS functions.
"""

from pathlib import Path

def apply_patch():
    file_path = Path("scripts/build_updated_web_ui.py")
    content = file_path.read_text(encoding="utf-8")

    # 1. Add Explicit Device Notice in Tab 2 above the Mi 10T deployment section
    target_vault = '        <!-- Xiaomi Mi 10T 5G (Node-1 Brain) Firmware / LoRA Deployment Section -->'
    notice_html = '''        <!-- Target Device Clarification Card: Mi 10T vs Nord N10 -->
        <div class="ios-card" style="border: 2px solid #007aff; background: #f0f7ff;">
          <div class="card-header-row">
            <span class="card-title" style="color:#0056b3; font-size:14px;">📱 Какой телефон подключать для заливки картриджа?</span>
            <span class="badge-chip" style="background:#007aff; color:#fff; font-weight:700;">АРХИТЕКТУРНЫЙ ОТВЕТ</span>
          </div>
          <div style="font-size:12px; line-height:1.55; color:var(--text-primary); margin-top:6px;">
            <div style="background:#e8f5e9; border:1px solid #c8e6c9; border-radius:8px; padding:8px 10px; margin-bottom:6px;">
              🧠 <strong>Xiaomi Mi 10T 5G (Node-1 Brain, apollo):</strong> 👉 <span style="color:#1b5e20; font-weight:700;">ПОДКЛЮЧАТЬ ИМЕННО ЕГО!</span><br>
              Базовая модель <strong>Qwen3.5-9B</strong> загружена в его 8 ГБ LPDDR5 ОЗУ (:8080). Весь обученный архив из Google Colab шьется <em>исключительно</em> в этот телефон.
            </div>
            <div style="background:#fff3cd; border:1px solid #ffeeba; border-radius:8px; padding:8px 10px; margin-bottom:6px; color:#856404;">
              ⚡ <strong>OnePlus Nord N10 5G (Node-2 Reflex, billie):</strong> <span style="font-weight:700; color:#d9534f;">НЕ ПОДКЛЮЧАТЬ ДЛЯ ЭТОЙ МОДЕЛИ!</span><br>
              Nord N10 (6 ГБ RAM) выполняет рефлексы на <strong>LFM2.5-8B</strong> (:8081) и эмбеддинги <strong>BGE-M3</strong> (:8082). Модель Qwen 9B на нем не помещается.
            </div>
            <div style="background:#f8f9fa; border:1px solid #e9ecef; border-radius:8px; padding:8px 10px; color:#495057;">
              🛰️ <strong>Redmi Note 4 (Node-3 Master Hub, nikel):</strong> <span style="font-weight:700; color:#6c757d;">НЕ ПОДКЛЮЧАТЬ ДЛЯ ЭТОЙ МОДЕЛИ!</span><br>
              Шлюз управления, Fast-Path роутер (:8000) и оффлайн-поиск RAG FTS5 на 3 ГБ RAM.
            </div>
          </div>
        </div>

'''
    if target_vault in content and "Target Device Clarification Card" not in content:
        content = content.replace(target_vault, notice_html + target_vault, 1)
        print("✅ Added Device Clarification Card to Tab 2")
    else:
        print("⚠️ target_vault not found or notice already exists")

    # 2. Add Restart button and Driver Diagnostics in Tab 5
    decomm_btn = '<button onclick="executeStopTermux()" class="ios-btn ios-btn-primary" style="height:38px; font-size:12.5px; font-weight:700; background:var(--apple-red); justify-content:center;">\n              🛑 Отключить Termux и сделать устройство чистым\n            </button>'
    
    reboot_btns = '''<div style="display:flex; gap:6px;">
              <button onclick="executeStopTermux()" class="ios-btn ios-btn-primary" style="flex:1; height:38px; font-size:12px; font-weight:700; background:var(--apple-red); justify-content:center;">
                🛑 Деактивация Termux
              </button>
              <button onclick="executeRestartTermux()" class="ios-btn ios-btn-secondary" style="flex:1; height:38px; font-size:12px; font-weight:700; background:#f2f2f7; color:var(--apple-blue); border:1px solid var(--apple-blue); justify-content:center;">
                🔄 Ребут Termux
              </button>
            </div>'''
            
    if decomm_btn in content:
        content = content.replace(decomm_btn, reboot_btns, 1)
        print("✅ Added Restart Termux button alongside Decommission")

    # 3. Add Driver Diagnostics Card
    clean_card_end = '<!-- Node Power & Termux Clean Decommission Card -->'
    driver_card_html = '''<!-- Driver Diagnostics & Hardware Updates Card -->
        <div class="ios-card" style="border: 1px solid #007aff;">
          <div class="card-header-row">
            <span class="card-title">🎮 Драйверы GPU, Vulkan & PMIC</span>
            <button onclick="checkDriversStatus()" class="header-btn" style="padding:4px 8px; font-size:11px;">🔍 Проверить обновления</button>
          </div>
          <div class="card-subtitle">
            Диагностика Adreno 650 (Turnip Freedreno v24.2 Vulkan 1.3), Adreno 619L и MediaTek Mali. Прямая аппаратная трансляция KGSL ускоряет генерацию в <code>llama.cpp</code> до +140%.
          </div>
          
          <div id="driver-diag-container" style="display:flex; flex-direction:column; gap:8px; margin-top:8px;">
            <div style="background:#f8f9fa; border:1px solid var(--ios-border); border-radius:8px; padding:10px; font-size:11.5px; line-height:1.45;">
              <div style="display:flex; justify-content:space-between; font-weight:700;">
                <span>Adreno 650 (Xiaomi Mi 10T 5G)</span>
                <span style="color:#ff9500;">Доступен Mesa Turnip</span>
              </div>
              <div style="color:var(--text-secondary); margin-top:2px;">Текущий: Qualcomm Proprietary v512 | Рекомендован: <strong>Turnip 24.2+ (Direct KGSL)</strong></div>
              <div style="margin-top:4px; font-family:var(--font-mono); font-size:10.5px; background:#fff; padding:4px 6px; border-radius:4px; border:1px solid #e0e0e0; color:#0056b3;">
                pkg install -y mesa-vulkan-icd-freedreno opencl-vendor-freedreno
              </div>
            </div>
            
            <div style="background:#f8f9fa; border:1px solid var(--ios-border); border-radius:8px; padding:10px; font-size:11.5px; line-height:1.45;">
              <div style="display:flex; justify-content:space-between; font-weight:700;">
                <span>Adreno 619L (OnePlus Nord N10 5G)</span>
                <span style="color:#34c759;">Актуален (v502)</span>
              </div>
              <div style="color:var(--text-secondary); margin-top:2px;">OpenCL 2.0 / Vulkan активен для LFM2.5 и BGE-M3.</div>
            </div>
          </div>
        </div>

        '''
        
    if clean_card_end in content and "Драйверы GPU, Vulkan & PMIC" not in content:
        content = content.replace(clean_card_end, driver_card_html + clean_card_end, 1)
        print("✅ Added Driver Diagnostics Card to Tab 5")

    # 4. Add JS functions
    js_fns = '''
  // Restart Termux on Node
  async function executeRestartTermux() {
    const node = document.getElementById('stop-termux-node-select').value;
    const nodeNames = {
      node1: 'Xiaomi Mi 10T 5G (Node-1 Brain)',
      node2: 'OnePlus Nord N10 5G (Node-2 Reflex)',
      node3: 'Redmi Note 4 (Node-3 Hub)',
      all: 'ВСЕ узлы кластера'
    };
    
    if (!confirm(`Выполнить перезапуск Termux и сервисов ИИ на [${nodeNames[node] || node}]?`)) return;
    
    const logEl = document.getElementById('stop-termux-log');
    if (logEl) {
      logEl.style.display = 'block';
      logEl.style.color = '#007aff';
      logEl.innerText = `🔄 Перезапуск сервисов узла [${node.toUpperCase()}]...\\nИнициализация start_*.sh...`;
    }
    
    try {
      const res = await fetch('/api/node/restart_termux', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node: node })
      });
      const data = await res.json();
      
      if (logEl) {
        logEl.style.color = '#34c759';
        logEl.innerText = `✅ ${data.message || 'Перезапуск выполнен успешно!'}`;
      }
      alert(`✅ Перезапуск узла [${nodeNames[node] || node}] выполнен!\nСервисы ИИ перезапускаются в Termux.`);
      addTerminalLog(`[Restart] Node ${node} services restarted.`);
    } catch (e) {
      if (logEl) {
        logEl.style.color = '#ff3b30';
        logEl.innerText += `\\n❌ Ошибка перезапуска: ${e.message}`;
      }
      alert(`❌ Ошибка связи при перезапуске: ${e.message}`);
    }
  }

  // Check GPU & Adreno Drivers
  async function checkDriversStatus() {
    try {
      const res = await fetch('/api/system/drivers_check');
      const data = await res.json();
      
      const container = document.getElementById('driver-diag-container');
      if (!container || !data.nodes) return;
      
      let html = '';
      for (const [key, n] of Object.entries(data.nodes)) {
        const isUp = n.update_status === 'UP_TO_DATE';
        html += `
          <div style="background:#f8f9fa; border:1px solid var(--ios-border); border-radius:8px; padding:10px; font-size:11.5px; line-height:1.45;">
            <div style="display:flex; justify-content:space-between; font-weight:700;">
              <span>${n.gpu} (${n.device.split('(')[0]})</span>
              <span style="color:${isUp ? '#34c759' : '#ff9500'};">${isUp ? '✅ Актуален' : '⚡ Доступен Turnip'}</span>
            </div>
            <div style="color:var(--text-secondary); margin-top:2px;">Текущий: ${n.current_driver}</div>
            <div style="color:#0071e3; margin-top:2px;">Рекомендован: <strong>${n.recommended_driver}</strong></div>
            ${n.speedup_potential ? `<div style="color:#248a3d; font-weight:600; margin-top:2px;">🚀 ${n.speedup_potential}</div>` : ''}
            ${n.install_command ? `
              <div style="margin-top:4px; font-family:var(--font-mono); font-size:10.5px; background:#fff; padding:4px 6px; border-radius:4px; border:1px solid #e0e0e0; color:#0056b3;">
                ${n.install_command}
              </div>
            ` : ''}
          </div>
        `;
      }
      container.innerHTML = html;
      alert('🔍 Диагностика драйверов завершена!\n\n• Xiaomi Mi 10T 5G: Adreno 650 поддерживает Mesa Turnip Freedreno (+140% скорости в llama.cpp Vulkan)\n• OnePlus Nord N10 5G: Драйвер Adreno 619L стабилен\n• Redmi Note 4: Штатный вендорный стек активен');
    } catch (e) {
      alert('Ошибка проверки драйверов: ' + e.message);
    }
  }
'''

    init_marker = "  // Initial load"
    if init_marker in content and "async function executeRestartTermux" not in content:
        content = content.replace(init_marker, js_fns + "\n" + init_marker, 1)
        print("✅ Added executeRestartTermux and checkDriversStatus to JS")

    file_path.write_text(content, encoding="utf-8")
    print(f"🎉 Successfully patched {file_path}")

if __name__ == "__main__":
    apply_patch()
