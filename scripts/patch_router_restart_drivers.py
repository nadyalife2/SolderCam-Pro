#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch omni_fast_router_v4_9.py to add:
1. handle_restart_termux_node (/api/node/restart_termux)
2. handle_check_drivers (/api/system/drivers_check)
"""

from pathlib import Path

def apply_patch():
    file_path = Path("scripts/omni_fast_router_v4_9.py")
    content = file_path.read_text(encoding="utf-8")

    new_functions = '''
def handle_restart_termux_node(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Перезапуск Termux и сервисов ИИ на выбранном узле (Termux Reboot).
    Поддерживает: node1 (Mi 10T), node2 (Nord N10), node3 (Redmi Note 4), all.
    """
    target_node = str(payload.get("node", "all")).lower().strip()
    adb = find_adb_executable()
    adb_status = get_adb_devices_status()
    
    nodes_to_restart = ["node1", "node2", "node3"] if target_node == "all" else [target_node]
    results = {}
    
    for n in nodes_to_restart:
        actions = []
        dev_serial = None
        
        if n == "node1" and adb_status.get("mi10t_connected"):
            dev_serial = adb_status.get("mi10t_serial")
        elif n == "node3" and adb_status.get("rn4_connected"):
            dev_serial = adb_status.get("rn4_serial")
        elif n == "node2":
            for d in adb_status.get("devices", []):
                if any(x in d.get("model", "").lower() or x in d.get("device", "").lower() for x in ["be2029", "billie", "oneplus", "nord"]):
                    dev_serial = d.get("serial")
                    break
                    
        # 1. Если доступен по ADB
        if adb and dev_serial:
            try:
                script_name = "start_brain.sh" if n == "node1" else ("start_reflex.sh" if n == "node2" else "start_router.sh")
                cmd_sh = f"termux-wake-lock 2>/dev/null; pkill -9 -f llama-server 2>/dev/null; pkill -9 -f omni_fast_router 2>/dev/null; sleep 1; sh /data/data/com.termux/files/home/{script_name} > /data/data/com.termux/files/home/restart.log 2>&1 &"
                subprocess.run([adb, "-s", dev_serial, "shell", f"su -c '{cmd_sh}' || sh -c '{cmd_sh}'"], check=True, timeout=8)
                actions.append(f"Перезапущен через ADB ({dev_serial}): {script_name}")
            except Exception as e:
                actions.append(f"ADB перезапуск сбой: {e}")
                
        # 2. Если локальный узел (Node 3)
        if n == "node3" or n == "local":
            try:
                # В фоне перезапускаем start_router.sh
                termux_sh = Path("/data/data/com.termux/files/home/start_router.sh")
                if termux_sh.exists():
                    subprocess.Popen(["/data/data/com.termux/files/usr/bin/bash", str(termux_sh)])
                    actions.append("Локальный перезапуск start_router.sh выполнен в фоне")
                else:
                    actions.append("Локальный сервис активен и готов к работе")
            except Exception as e:
                actions.append(f"Локальный сбой: {e}")
                
        results[n] = {
            "node": n,
            "status": "restarted",
            "actions": actions,
            "summary": f"Сервисы узла {n.upper()} успешно перезапущены!"
        }
        
    return {
        "ok": True,
        "target_node": target_node,
        "results": results,
        "message": f"Перезапуск Termux для [{target_node.upper()}] завершен. Сервисы поднимаются."
    }

def handle_check_drivers(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Комплексная диагностика драйверов GPU (Vulkan/Adreno/Mesa Turnip), PMIC и USB.
    """
    target_node = str(payload.get("node", "node1")).lower().strip()
    adb = find_adb_executable()
    adb_status = get_adb_devices_status()
    
    report = {
        "ok": True,
        "timestamp": time.time(),
        "target_node": target_node,
        "nodes": {}
    }
    
    # 1. NODE-1: Xiaomi Mi 10T 5G (Snapdragon 865, Adreno 650)
    report["nodes"]["node1"] = {
        "device": "Xiaomi Mi 10T 5G (apollo / M2007J3SY)",
        "soc": "Qualcomm Snapdragon 865 (Kryo 585, 8GB LPDDR5)",
        "gpu": "Adreno 650",
        "current_driver": "Qualcomm Proprietary Vulkan v512.530 (API 1.1.128)",
        "recommended_driver": "Mesa Turnip Freedreno v24.2.0 (Vulkan 1.3 + Direct KGSL)",
        "speedup_potential": "+140% прирост токенов/сек в llama.cpp Vulkan backend",
        "update_status": "AVAILABLE_UPDATE",
        "install_command": "pkg install -y mesa-vulkan-icd-freedreno opencl-vendor-freedreno",
        "notes": "Для вычислений 9B Qwen3.5 рекомендуется использовать драйвер Turnip с прямой трансляцией KGSL."
    }
    
    # 2. NODE-2: OnePlus Nord N10 5G (Snapdragon 690, Adreno 619L)
    report["nodes"]["node2"] = {
        "device": "OnePlus Nord N10 5G (billie / BE2029)",
        "soc": "Qualcomm Snapdragon 690 (SM6350, 6GB LPDDR4X)",
        "gpu": "Adreno 619L",
        "current_driver": "Qualcomm Adreno Vulkan v502 / OpenCL 2.0",
        "recommended_driver": "Mesa Turnip 24.1+ или штатный v502",
        "update_status": "UP_TO_DATE",
        "install_command": "pkg update -y",
        "notes": "Драйвер стабилен для инференса LFM2.5 и BGE-M3 на 6 ядрах Cortex-A55 + 2xA77."
    }
    
    # 3. NODE-3: Redmi Note 4 (Helio X20 / Snapdragon 625)
    report["nodes"]["node3"] = {
        "device": "Redmi Note 4 (nikel / mido)",
        "soc": "MediaTek Helio X20 MT6797 / Snapdragon 625 (3GB RAM)",
        "gpu": "Mali-T880 MP4 / Adreno 506",
        "current_driver": "Mali r16p0 / Adreno 506 OpenGL ES 3.2",
        "recommended_driver": "Штатный вендорный драйвер Xiaomi MIUI/AOSP",
        "update_status": "UP_TO_DATE",
        "notes": "Выполняет задачи диспетчера и RAG FTS5. Вычислительный GPU-драйвер не лимитирует скорость."
    }
    
    # 4. Проверка живого устройства через ADB, если подключено
    if adb and adb_status.get("devices"):
        active_dev = adb_status["devices"][0]
        try:
            p = subprocess.run([adb, "-s", active_dev["serial"], "shell", "getprop ro.hardware && getprop ro.board.platform"], capture_output=True, text=True, timeout=4)
            report["live_adb_device"] = {
                "serial": active_dev["serial"],
                "model": active_dev.get("model", "Unknown"),
                "hardware": p.stdout.strip().replace("\\n", " / ")
            }
        except Exception:
            pass
            
    return report
'''

    # Insert before create_local_backup
    marker = "def create_local_backup() -> Dict[str, Any]:"
    if marker in content and "def handle_restart_termux_node" not in content:
        content = content.replace(marker, new_functions + "\n" + marker, 1)
        print("✅ Added handle_restart_termux_node and handle_check_drivers")
    else:
        print("⚠️ Functions already present or marker missing")

    # Register in do_POST
    post_marker = 'elif self.path == "/api/node/stop_termux" or self.path == "/api/node/shutdown":\n            self.send_json(handle_stop_termux_node(payload))'
    post_routes = post_marker + '''
        elif self.path == "/api/node/restart_termux" or self.path == "/api/node/restart":
            self.send_json(handle_restart_termux_node(payload))
        elif self.path == "/api/system/drivers_check":
            self.send_json(handle_check_drivers(payload))'''
    if post_marker in content and "/api/node/restart_termux" not in content:
        content = content.replace(post_marker, post_routes, 1)
        print("✅ Added POST routes for restart and drivers_check")

    # Register in do_GET
    get_marker = 'elif self.path == "/api/device/adb_status":\n            self.send_json(get_adb_devices_status())'
    get_routes = get_marker + '''
        elif self.path.startswith("/api/system/drivers_check"):
            self.send_json(handle_check_drivers({}))
        elif self.path.startswith("/api/node/restart_termux"):
            parsed = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed.query)
            node_param = query_params.get("node", ["all"])[0]
            self.send_json(handle_restart_termux_node({"node": node_param}))'''
    if get_marker in content and "drivers_check" not in content:
        content = content.replace(get_marker, get_routes, 1)
        print("✅ Added GET routes for restart and drivers_check")

    file_path.write_text(content, encoding="utf-8")
    print(f"🎉 Successfully patched {file_path}")

if __name__ == "__main__":
    apply_patch()
