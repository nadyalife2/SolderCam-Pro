#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch build_updated_web_ui.py to add Termux Clean Shutdown / Decommissioning card
into Tab 5 (Master Hub) and the executeStopTermux JavaScript function.
"""

from pathlib import Path

def apply_web_ui_patch():
    file_path = Path("scripts/build_updated_web_ui.py")
    content = file_path.read_text(encoding="utf-8")

    # 1. Insert Node Power & Termux Clean Decommission Card
    term_marker = '        <!-- Live Terminal Stream -->'
    
    clean_card_html = '''        <!-- Node Power & Termux Clean Decommission Card -->
        <div class="ios-card" style="border: 2px solid #ff3b30; background: #fffdfd;">
          <div class="card-header-row">
            <span class="card-title" style="color:var(--apple-red);">🧹 Деактивация Termux и очистка устройств</span>
            <span class="badge-chip" style="background:#fee2e2; color:#b91c1c; font-weight:700;">Clean State</span>
          </div>
          <div class="card-subtitle" style="margin-bottom:8px; line-height:1.45;">
            Выгружает ИИ-процессы (<code>llama-server</code>, <code>python</code>, <code>bge</code>), удаляет весь временный мусор (<code>/tmp/*</code>, <code>.cache</code>), снимает WakeLock процессора (<code>termux-wake-unlock</code>) и восстанавливает штатный режим зарядки батареи. <strong>Смартфон становится полностью чистым, холодным и возвращается к обычному режиму.</strong>
          </div>

          <div style="display:flex; flex-direction:column; gap:8px;">
            <div>
              <label style="font-size:11px; font-weight:600; color:var(--text-secondary); display:block; margin-bottom:3px;">Выберите целевое устройство:</label>
              <select id="stop-termux-node-select" class="ios-btn ios-btn-secondary" style="width:100%; font-size:12px; padding:6px 10px; background:#fff; border:1px solid #d1d1d6; color:var(--text-primary); cursor:pointer;">
                <option value="node1">NODE-1: Xiaomi Mi 10T 5G (Snapdragon 865, 8GB RAM, :8080)</option>
                <option value="node2">NODE-2: OnePlus Nord N10 5G (Snapdragon 690, 6GB RAM, :8081)</option>
                <option value="node3">NODE-3: Redmi Note 4 (Helio X20 / SD625, :8000)</option>
                <option value="all" selected>⚡ ВСЕ УЗЛЫ КЛАСТЕРА (Полный сброс всех 3 устройств)</option>
              </select>
            </div>

            <div>
              <label style="font-size:11px; font-weight:600; color:var(--text-secondary); display:block; margin-bottom:3px;">Режим отключения:</label>
              <select id="stop-termux-mode-select" class="ios-btn ios-btn-secondary" style="width:100%; font-size:12px; padding:6px 10px; background:#fff; border:1px solid #d1d1d6; color:var(--text-primary); cursor:pointer;">
                <option value="clean_stop" selected>🛑 Полная деактивация: выгрузить Termux, очистить RAM, снять WakeLock, телефон чист</option>
                <option value="soft_reset">⚡ Мягкий сброс: остановить ИИ-сервисы, освободить RAM, но оставить Termux открытым</option>
                <option value="restore_battery">🔋 Только батарея: вернуть штатную зарядку, отключить байпас PMIC</option>
              </select>
            </div>

            <button onclick="executeStopTermux()" class="ios-btn ios-btn-primary" style="height:38px; font-size:12.5px; font-weight:700; background:var(--apple-red); justify-content:center;">
              🛑 Отключить Termux и сделать устройство чистым
            </button>

            <!-- Execution log output -->
            <div id="stop-termux-log" style="display:none; font-family:var(--font-mono); font-size:11px; background:#1c1c1e; color:#ff6b6b; padding:8px 10px; border-radius:6px; max-height:130px; overflow-y:auto; white-space:pre-wrap; line-height:1.35;"></div>
          </div>
        </div>

'''

    if term_marker in content and "Деактивация Termux и очистка устройств" not in content:
        content = content.replace(term_marker, clean_card_html + term_marker, 1)
        print("✅ Added Termux Clean Decommission Card into Master Hub tab")
    else:
        print("⚠️ Card already present or term_marker not found")

    # 2. Add executeStopTermux JavaScript function
    js_fn = '''
  // Execute Termux Clean Decommission & Shutdown
  async function executeStopTermux() {
    const node = document.getElementById('stop-termux-node-select').value;
    const mode = document.getElementById('stop-termux-mode-select').value;
    
    const nodeNames = {
      node1: 'Xiaomi Mi 10T 5G (Node-1 Brain)',
      node2: 'OnePlus Nord N10 5G (Node-2 Reflex)',
      node3: 'Redmi Note 4 (Node-3 Hub)',
      all: 'ВСЕ устройства кластера'
    };
    
    const confirmMsg = `Подтвердите действие:\\n\\n• Устройство: ${nodeNames[node] || node}\\n• Режим: ${mode}\\n\\nTermux будет деактивирован, память LPDDR освобождена, временные файлы удалены, а телефон вернется в чистый штатный режим.\\n\\nПродолжить?`;
    if (!confirm(confirmMsg)) return;
    
    const logEl = document.getElementById('stop-termux-log');
    if (logEl) {
      logEl.style.display = 'block';
      logEl.style.color = '#ff9500';
      logEl.innerText = `⏳ Отправка команды деактивации на [${node.toUpperCase()}]...\\nРежим: ${mode}...`;
    }
    
    addTerminalLog(`[Cluster Decommission] Initiated shutdown for ${node} (mode: ${mode})...`);
    
    try {
      const res = await fetch('/api/node/stop_termux', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node: node, mode: mode })
      });
      const data = await res.json();
      
      if (logEl) {
        logEl.style.color = '#34c759';
        let detail = `✅ ${data.message || 'Очистка успешно выполнена!'}\\n`;
        if (data.results) {
          for (const [k, v] of Object.entries(data.results)) {
            detail += `\\n• ${k.toUpperCase()}: ${v.summary || 'Очищен'}`;
            if (v.actions && v.actions.length) {
              v.actions.forEach(a => detail += `\\n   - ${a}`);
            }
          }
        }
        logEl.innerText = detail;
      }
      
      alert(`✅ Устройство [${nodeNames[node] || node}] успешно очищено!\\n\\nИИ-процессы выгружены из памяти, WakeLock снят, временные файлы удалены, батарея переведена в обычный режим.`);
      addTerminalLog(`[Cluster Decommission] Node ${node} successfully decommissioned to pristine state.`);
    } catch (e) {
      if (logEl) {
        logEl.style.color = '#ff3b30';
        logEl.innerText += `\\n❌ Сетевая ошибка: ${e.message}`;
      }
      alert(`❌ Ошибка отправки команды: ${e.message}`);
    }
  }
'''

    init_marker = "  // Initial load"
    if init_marker in content and "async function executeStopTermux" not in content:
        content = content.replace(init_marker, js_fn + "\n" + init_marker, 1)
        print("✅ Added executeStopTermux JavaScript function")
    else:
        print("⚠️ executeStopTermux already present or init_marker missing")

    file_path.write_text(content, encoding="utf-8")
    print(f"🎉 Successfully patched {file_path}")

if __name__ == "__main__":
    apply_web_ui_patch()
