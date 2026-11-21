with open("scripts/omni_fast_router_v4_9.py", "r", encoding="utf-8") as f:
    text = f.read()

target = '        elif self.path == "/api/device/adb_status":\n            self.send_json(get_adb_devices_status())'
add_lines = '''        elif self.path == "/api/device/adb_status":
            self.send_json(get_adb_devices_status())
        elif self.path.startswith("/api/system/drivers_check"):
            self.send_json(handle_check_drivers({}))
        elif self.path.startswith("/api/node/restart_termux"):
            parsed = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed.query)
            node_param = query_params.get("node", ["all"])[0]
            self.send_json(handle_restart_termux_node({"node": node_param}))'''

if target in text and "/api/system/drivers_check" not in text[text.find(target):text.find(target)+300]:
    text = text.replace(target, add_lines, 1)
    with open("scripts/omni_fast_router_v4_9.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("✅ Added drivers_check and restart_termux to do_GET")
else:
    print("⚠️ Already added or target missing")
