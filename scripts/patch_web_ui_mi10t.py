#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust Patch build_updated_web_ui.py to add Xiaomi Mi 10T 5G (Node-1 Brain)
dedicated flashing interface and real-time ADB connection status detection.
"""

from pathlib import Path

def apply_patch():
    file_path = Path("scripts/build_updated_web_ui.py")
    content = file_path.read_text(encoding="utf-8")

    # Replace checkAdbDeviceStatus and loadLocalCartridgesList with robust versions
    idx_start = content.find("  // ================= Xiaomi Mi 10T 5G (Node-1) Deployment & ADB Status =================")
    idx_end = content.find("  // Initial load")
    if idx_start != -1 and idx_end != -1:
        new_js_block = '''  // ================= Xiaomi Mi 10T 5G (Node-1) Deployment & ADB Status =================
  let gAdbStatus = null;

  async function checkAdbDeviceStatus(silent = false) {
    try {
      const res = await fetch('/api/device/adb_status');
      if (!res.ok) return;
      const data = await res.json();
      gAdbStatus = data;
      
      const badge = document.getElementById('mi10t-adb-badge');
      const banner = document.getElementById('mi10t-connection-banner');
      const btn = document.getElementById('btn-deploy-mi10t');
      
      if (!badge || !banner) return;
      
      if (data.mi10t_connected) {
        badge.innerText = '✅ Mi 10T Подключен';
        badge.style.background = 'var(--apple-green)';
        badge.style.color = '#fff';
        
        const dev = (data.devices && data.mi10t_serial) ? data.devices.find(d => d.serial === data.mi10t_serial) : (data.mi10t_device || {});
        banner.style.background = '#e8f5e9';
        banner.style.color = '#1b5e20';
        banner.style.border = '1px solid #c8e6c9';
        banner.innerHTML = `✅ <strong>Обнаружен целевой мозг:</strong> Xiaomi Mi 10T 5G (Серийник: <code>${data.mi10t_serial || (dev && dev.serial) || 'apollo'}</code>, Модель: <code>${(dev && dev.model) || 'apollo'}</code>).<br>Устройство готово к заливке весов и адаптеров LoRA в Termux LPDDR5!`;
        if (btn) btn.disabled = false;
      } else {
        badge.innerText = '⚠️ Подключите Mi 10T';
        badge.style.background = '#ff9500';
        badge.style.color = '#fff';
        
        banner.style.background = '#fff3cd';
        banner.style.color = '#856404';
        banner.style.border = '1px solid #ffeeba';
        
        let otherInfo = 'Устройств не обнаружено';
        const devs = data.devices || data.other_devices || [];
        if (devs.length > 0) {
          otherInfo = devs.map(d => `${d.model || 'Device'} (${d.serial})`).join(', ');
        }
        banner.innerHTML = `⚠️ <strong>Внимание!</strong> Для обновления модели необходимо подключить к ПК по USB <strong>Xiaomi Mi 10T 5G</strong> (Node-1 Brain).<br>Сейчас по USB подключено: <em>${otherInfo}</em>. Переподключите кабель к Mi 10T 5G!`;
      }
    } catch (e) {
      console.warn('ADB status check failed:', e);
    }
  }

  async function loadLocalCartridgesList() {
    try {
      const res = await fetch('/api/cartridge/list_local');
      if (!res.ok) return;
      const data = await res.json();
      const sel = document.getElementById('mi10t-cartridge-select');
      if (!sel) return;
      
      const items = Array.isArray(data) ? data : (data.cartridges || []);
      if (!items || items.length === 0) {
        sel.innerHTML = '<option value="">-- В папке cartridges/ нет файлов .omni.zip --</option>';
        return;
      }
      
      sel.innerHTML = items.map(c => {
        const fname = c.filename || c.name || 'cartridge.omni.zip';
        const isSelected = fname.includes('triad-omni-fast-tool') ? 'selected' : '';
        const size = c.size_mb || 0;
        const tag = (c.card && c.card.build_tag) || c.build_tag || '';
        return `<option value="${c.path}" ${isSelected}>📦 ${fname} (${size} MB${tag ? ' - ' + tag : ''})</option>`;
      }).join('');
    } catch (e) {
      console.warn('Cartridge list fetch failed:', e);
    }
  }

  function refreshAdbAndCartridges() {
    checkAdbDeviceStatus();
    loadLocalCartridgesList();
  }

  async function deploySelectedCartridgeToMi10t() {
    const sel = document.getElementById('mi10t-cartridge-select');
    const path = sel ? sel.value : '';
    if (!path) {
      alert('⚠️ Сначала выберите файл .omni.zip для прошивки!');
      return;
    }
    
    if (gAdbStatus && !gAdbStatus.mi10t_connected) {
      const ok = confirm('⚠️ Внимание: Xiaomi Mi 10T 5G сейчас НЕ обнаружен в ADB!\\n(Обнаружено другое устройство или пусто).\\n\\nВы уверены, что хотите продолжить заливку картриджа на подключенное устройство?');
      if (!ok) return;
    }
    
    const progressEl = document.getElementById('mi10t-deploy-progress');
    if (progressEl) {
      progressEl.style.display = 'block';
      progressEl.innerText = `🚀 Инициализация прошивки картриджа в Xiaomi Mi 10T 5G...\\n📦 Файл: ${path}\\n[1/4] Распаковка архива и проверка контрольных сумм...`;
    }
    
    addTerminalLog(`[Mi 10T Deploy] Starting deployment of ${path.split(/[\\\\/]/).pop()}...`);
    
    try {
      const res = await fetch('/api/cartridge/deploy_mi10t', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cartridge_path: path })
      });
      const data = await res.json();
      
      if (progressEl) {
        if (data.status === 'ok') {
          progressEl.innerText += `\\n[2/4] Верификация card.json (Schema: ${data.card ? data.card.schema_version : 'omni.lora.card/1'}) - OK!\\n[3/4] ${data.message}\\n[4/4] ✅ Прошивка в Mi 10T завершена успешно!`;
          alert(`✅ Успех!\\nКартридж успешно прошит в Xiaomi Mi 10T 5G!\\n\\n${data.message}`);
          loadCartridgeVault();
        } else {
          progressEl.innerText += `\\n❌ Ошибка: ${data.message || 'Сбой заливки'}`;
          alert(`❌ Ошибка прошивки в Mi 10T:\\n${data.message}`);
        }
      }
      addTerminalLog(`[Mi 10T Deploy] Finished: ${data.status} - ${data.message}`);
    } catch (e) {
      if (progressEl) progressEl.innerText += `\\n❌ Сетевая ошибка при вызове /api/cartridge/deploy_mi10t: ${e.message}`;
      alert(`❌ Ошибка связи с роутером: ${e.message}`);
    }
  }

'''
        content = content[:idx_start] + new_js_block + content[idx_end:]
        file_path.write_text(content, encoding="utf-8")
        print("✅ Refined JS block in build_updated_web_ui.py")
        return True

    print("⚠️ Nothing replaced")
    return False

if __name__ == "__main__":
    apply_patch()
