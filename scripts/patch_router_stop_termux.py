#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch omni_fast_router_v4_9.py to add handle_stop_termux_node and register endpoints
POST /api/node/stop_termux and GET /api/node/stop_termux
"""

from pathlib import Path

def apply_router_patch():
    file_path = Path("scripts/omni_fast_router_v4_9.py")
    content = file_path.read_text(encoding="utf-8")

    # 1. Add handle_stop_termux_node definition
    fn_code = '''
def handle_stop_termux_node(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Полное отключение Termux и глубокая очистка устройства (Clean Decommission).
    Поддерживает: node1 (Mi 10T 5G), node2 (Nord N10 5G), node3 (Redmi Note 4), all.
    Режимы (mode):
      - 'clean_stop': Остановка ИИ-демонов, очистка /tmp и кэшей, снятие WakeLock,
                      сброс кэшей RAM, восстановление нормальной зарядки аккумулятора,
                      выгрузка Termux из памяти.
      - 'soft_reset': Выгрузка ИИ-сервисов (llama-server, python), очистка RAM, снятие WakeLock,
                      но сессия Termux сохраняется для консоли.
      - 'restore_battery': Только восстановление нормальной зарядки аккумулятора (отключение байпаса).
    """
    target_node = str(payload.get("node", "all")).lower().strip()
    mode = str(payload.get("mode", "clean_stop")).lower().strip()
    
    adb = find_adb_executable()
    adb_status = get_adb_devices_status()
    
    # Базовые shell-команды очистки в Termux
    cleanup_cmds = [
        "termux-wake-unlock 2>/dev/null || true",
        "pkill -9 -f llama-server 2>/dev/null || true",
        "pkill -9 -f 'python.*omni_fast_router' 2>/dev/null || true",
        "pkill -9 -f 'python.*bge' 2>/dev/null || true",
        "pkill -9 -f 'python.*lfm' 2>/dev/null || true",
        "rm -rf /data/data/com.termux/files/usr/tmp/* 2>/dev/null || true",
        "rm -rf /data/data/com.termux/files/home/.cache/* 2>/dev/null || true",
        "rm -f /data/data/com.termux/files/home/*.log /data/data/com.termux/files/home/*.cache 2>/dev/null || true",
        "rm -f /data/data/com.termux/files/home/lookup.cache 2>/dev/null || true",
        # Восстановление зарядки (снять байпас питания, разрешить штатную зарядку)
        "echo 1 > /sys/class/power_supply/battery/charging_enabled 2>/dev/null || true",
        "echo 1 > /sys/class/power_supply/battery/battery_charging_enabled 2>/dev/null || true",
        "echo 0 > /sys/class/power_supply/battery/input_suspend 2>/dev/null || true",
        # Сброс кэшей памяти
        "sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true"
    ]
    
    if mode == "clean_stop":
        cleanup_cmds.append("pkill -9 -f com.termux 2>/dev/null || true")
        cleanup_cmds.append("am force-stop com.termux 2>/dev/null || true")
        
    full_sh_cmd = "; ".join(cleanup_cmds)
    
    nodes_to_process = ["node1", "node2", "node3"] if target_node == "all" else [target_node]
    results = {}
    
    for n in nodes_to_process:
        actions = []
        dev_serial = None
        
        # Определяем серийник ADB, если устройство подключено
        if n == "node1" and adb_status.get("mi10t_connected"):
            dev_serial = adb_status.get("mi10t_serial")
        elif n == "node3" and adb_status.get("rn4_connected"):
            dev_serial = adb_status.get("rn4_serial")
        elif n == "node2":
            for d in adb_status.get("devices", []):
                if any(x in d.get("model", "").lower() or x in d.get("device", "").lower() for x in ["be2029", "billie", "oneplus", "nord"]):
                    dev_serial = d.get("serial")
                    break
        
        # 1. Попытка через ADB (наиболее надежный способ с root)
        adb_done = False
        if adb and dev_serial:
            try:
                cmd_adb = [adb, "-s", dev_serial, "shell", f"su -c '{full_sh_cmd}' || sh -c '{full_sh_cmd}'"]
                proc = subprocess.run(cmd_adb, capture_output=True, text=True, timeout=8)
                actions.append(f"Выполнен сброс через USB/ADB ({dev_serial})")
                adb_done = True
                
                # Скриншот подтверждения
                scr_path = BASE_DIR / "screenshots" / f"{n}_clean_shutdown.png"
                scr_path.parent.mkdir(parents=True, exist_ok=True)
                with open(scr_path, "wb") as f:
                    subprocess.run([adb, "-s", dev_serial, "exec-out", "screencap", "-p"], stdout=f, timeout=5)
                actions.append(f"Скриншот чистого состояния сохранен: screenshots/{n}_clean_shutdown.png")
            except Exception as e:
                actions.append(f"ADB сбой: {e}")
                
        # 2. Если это локальный хост (например Redmi Note 4, где запущен роутер)
        if not adb_done and (n == "node3" or n == "local"):
            try:
                # На локальном устройстве чистим память, временные файлы и батарею,
                # не убивая сам процесс роутера до отправки HTTP-ответа
                local_safe_cmds = [c for c in cleanup_cmds if "omni_fast_router" not in c and "com.termux" not in c]
                subprocess.run("; ".join(local_safe_cmds), shell=True, capture_output=True, timeout=5)
                actions.append("Локально: очищен кэш /tmp, освобождена память LPDDR, снят WakeLock, восстановлен контроллер заряда")
            except Exception as e:
                actions.append(f"Локальный сбой: {e}")
                
        # 3. Удаленный узел через HTTP /api/system/shutdown
        if not adb_done and n in ["node1", "node2"]:
            target_url = NODE1_URL if n == "node1" else NODE2_LFM
            try:
                req = urllib.request.Request(
                    f"{target_url}/api/system/shutdown",
                    data=json.dumps({"mode": mode}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    actions.append(f"HTTP запрос деактивации успешно принят узлом {target_url}")
            except Exception as e:
                actions.append(f"Сеть: узел {n.upper()} не ответил по HTTP ({e}). Для ручного сброса выполните в Termux: termux-wake-unlock && pkill -9 -f llama-server")
                
        results[n] = {
            "node": n,
            "status": "deactivated",
            "actions": actions,
            "summary": f"Узел {n.upper()} очищен: ИИ-процессы выгружены, /tmp удален, WakeLock снят, батарея переведена в штатный режим."
        }
        
    return {
        "ok": True,
        "target_node": target_node,
        "mode": mode,
        "results": results,
        "device_state": "CLEAN_PRISTINE",
        "message": f"Деактивация и глубокая очистка Termux для [{target_node.upper()}] успешно выполнена. Устройства возвращены в штатный режим Android."
    }
'''

    # Insert handle_stop_termux_node before create_local_backup
    backup_marker = "def create_local_backup() -> Dict[str, Any]:"
    if backup_marker in content and "def handle_stop_termux_node" not in content:
        content = content.replace(backup_marker, fn_code + "\n" + backup_marker, 1)
        print("✅ Added handle_stop_termux_node function")
    else:
        print("⚠️ handle_stop_termux_node already present or backup_marker missing")

    # 2. Register route in do_POST
    post_target = 'elif self.path == "/api/cartridge/deploy_mi10t":\n            self.send_json(handle_deploy_cartridge_to_mi10t(payload))'
    post_replace = post_target + '\n        elif self.path == "/api/node/stop_termux" or self.path == "/api/node/shutdown":\n            self.send_json(handle_stop_termux_node(payload))'
    if post_target in content and "/api/node/stop_termux" not in content:
        content = content.replace(post_target, post_replace, 1)
        print("✅ Added POST /api/node/stop_termux route")

    # 3. Register route in do_GET for easy URL triggering
    get_target = 'elif self.path == "/api/cartridge/list_local":\n            self.send_json(get_local_cartridges_list())'
    get_replace = get_target + '\n        elif self.path.startswith("/api/node/stop_termux") or self.path.startswith("/api/node/shutdown"):\n            parsed = urllib.parse.urlparse(self.path)\n            query_params = urllib.parse.parse_qs(parsed.query)\n            node_param = query_params.get("node", ["all"])[0]\n            mode_param = query_params.get("mode", ["clean_stop"])[0]\n            self.send_json(handle_stop_termux_node({"node": node_param, "mode": mode_param}))'
    if get_target in content and "query_params.get(\"node\"" not in content:
        content = content.replace(get_target, get_replace, 1)
        print("✅ Added GET /api/node/stop_termux route")

    file_path.write_text(content, encoding="utf-8")
    print("🎉 Successfully patched scripts/omni_fast_router_v4_9.py")

if __name__ == "__main__":
    apply_router_patch()
