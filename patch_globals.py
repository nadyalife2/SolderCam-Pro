# -*- coding: utf-8 -*-
import os, sys, json, ast

target_file = 'd:/для one plus nord n10/omni_gateway.py'
with open(target_file, 'r', encoding='utf-8') as f:
    code = f.read()

# Add import urllib.parse if not present
if 'import urllib.parse' not in code:
    code = code.replace('import urllib.request', 'import urllib.request\nimport urllib.parse')

insert_block = '''
# ----------------- GLOBAL STATE & HELPERS -----------------
CURRENT_MODE = "9b"
MODE_LABELS = {
    "9b": "9B Автономно (Xiaomi)",
    "33b_rpc": "33B RPC Mi10T + ПК",
    "33b_hybrid": "33B Учитель Hybrid (ПК)"
}
TELEMETRY_CACHE = {}
LAST_ALERT = {"type": None, "ts": 0}

def add_log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        conn.execute("INSERT INTO logs (ts, level, msg) VALUES (?, ?, ?)", (ts, level, msg))
        conn.commit()
    except Exception:
        pass
    print(f"[{ts}] [{level}] {msg}")

def http_json(url, data=None, timeout=10):
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers=headers
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

# Загрузка каталога Awesome-REA
REA_TOOLS = []
for p in ['/sdcard/OmniCluster_Data/tool-resources.json', '~/tool-resources.json', 'd:/для one plus nord n10/.agents/skills/awesome-rea/data/tool-resources.json']:
    expanded = os.path.expanduser(p)
    if os.path.exists(expanded):
        try:
            with open(expanded, 'r', encoding='utf-8') as rf:
                REA_TOOLS = json.load(rf)
                print(f'Awesome-REA loaded: {len(REA_TOOLS)} tools from {expanded}')
                break
        except Exception as e:
            print('REA load error:', e)

def get_local_telemetry():
    batt = 100
    temp = 32.0
    free_ram = 1200
    try:
        if os.path.exists('/sys/class/power_supply/battery/capacity'):
            with open('/sys/class/power_supply/battery/capacity') as f:
                batt = int(f.read().strip())
        if os.path.exists('/sys/class/power_supply/battery/batt_temp'):
            with open('/sys/class/power_supply/battery/batt_temp') as f:
                temp = round(int(f.read().strip()) / 10.0, 1)
        elif os.path.exists('/sys/class/power_supply/battery/temp'):
            with open('/sys/class/power_supply/battery/temp') as f:
                temp = round(int(f.read().strip()) / 10.0, 1)
        if os.path.exists('/proc/meminfo'):
            with open('/proc/meminfo') as f:
                for l in f:
                    if 'MemAvailable' in l:
                        free_ram = round(int(l.split()[1]) / 1024.0, 1)
                        break
    except Exception:
        pass
    return {
        "online": True,
        "battery": batt,
        "temp_c": temp,
        "free_ram_mb": free_ram
    }

def telemetry_watchdog_thread():
    global LAST_ALERT
    while True:
        try:
            loc = get_local_telemetry()
            TELEMETRY_CACHE["note4"] = loc
            
            # Check Mi10T
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                res = s.connect_ex((NODES["mi10t"]["ip"], NODES["mi10t"]["port"]))
                s.close()
                NODES["mi10t"]["online"] = (res == 0)
                if "mi10t" not in TELEMETRY_CACHE:
                    TELEMETRY_CACHE["mi10t"] = {"online": (res == 0), "battery": 88, "temp_c": 34.5, "free_ram_mb": 4200}
                else:
                    TELEMETRY_CACHE["mi10t"]["online"] = (res == 0)
            except Exception:
                NODES["mi10t"]["online"] = False
                if "mi10t" in TELEMETRY_CACHE:
                    TELEMETRY_CACHE["mi10t"]["online"] = False

            # Check Nord N10
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                res = s.connect_ex((NODES["nord10"]["ip"], NODES["nord10"]["port"]))
                s.close()
                NODES["nord10"]["online"] = (res == 0)
                if "nord10" not in TELEMETRY_CACHE:
                    TELEMETRY_CACHE["nord10"] = {"online": (res == 0), "battery": 92, "temp_c": 31.0, "free_ram_mb": 3100}
                else:
                    TELEMETRY_CACHE["nord10"]["online"] = (res == 0)
            except Exception:
                NODES["nord10"]["online"] = False
                if "nord10" in TELEMETRY_CACHE:
                    TELEMETRY_CACHE["nord10"]["online"] = False

            # Check PC
            TELEMETRY_CACHE["pc"] = {"online": False, "battery": -1, "temp_c": 42.0, "free_ram_mb": 9500}
            
            if loc.get("temp_c", 0) > 46.0:
                LAST_ALERT = {"type": "overheat", "msg": f"Перегрев Redmi Note 4: {loc['temp_c']}°C!", "ts": time.time()}
        except Exception:
            pass
        time.sleep(3)

threading.Thread(target=telemetry_watchdog_thread, daemon=True).start()
'''

target_marker = '# ----------------- HTTP REQUEST HANDLER -----------------'
if target_marker in code:
    code = code.replace(target_marker, insert_block + '\n' + target_marker)
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(code)
    print('SUCCESSFULLY PATCHED omni_gateway.py')
else:
    print('Target marker not found!')
