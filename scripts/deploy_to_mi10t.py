import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(r"d:\для one plus nord n10")
ADAPTER_PATH = BASE_DIR / "models" / "adapter.gguf"
CARD_PATH = BASE_DIR / "models" / "card.json"
SCREENSHOT_PATH = BASE_DIR / "screenshots" / "mi10t_cartridge_deployed.png"

ADB_PATH = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def run_adb(cmd_list):
    full_cmd = [ADB_PATH] + cmd_list
    res = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return res.returncode, res.stdout.strip(), res.stderr.strip()

print("🔍 Checking ADB devices...")
rc, out, err = run_adb(["devices"])
print(out)

devices = [line.split()[0] for line in out.splitlines()[1:] if line.strip() and "device" in line]

if not devices:
    print("❌ No ADB device detected. Please connect Xiaomi Mi 10T via USB and enable USB Debugging.")
    sys.exit(1)

dev_id = devices[0]
print(f"✅ Found target device: {dev_id} (Xiaomi Mi 10T 5G / apollo)")

card_data = {}
if CARD_PATH.exists():
    try:
        with open(CARD_PATH, "r", encoding="utf-8") as f:
            card_data = json.load(f)
    except Exception:
        pass

slug = card_data.get("slug", "triad-omni-cartridge")
build_tag = card_data.get("build_tag", card_data.get("version", "v1.0"))

TERMUX_HOME = "/data/data/com.termux/files/home"
TARGET_DIR = f"{TERMUX_HOME}/cartridges/{build_tag}"
MODELS_DIR = f"{TERMUX_HOME}/models"
CONFIG_DIR = f"{TERMUX_HOME}/config"

print("1. Creating directories in Termux...")
run_adb(["shell", f"mkdir -p {TARGET_DIR} {MODELS_DIR} {CONFIG_DIR}"])

print(f"2. Pushing adapter.gguf ({ADAPTER_PATH.stat().st_size / (1024*1024):.2f} MB) via ADB USB...")
t0 = time.time()
full_cmd = [ADB_PATH, "push", str(ADAPTER_PATH), f"{TARGET_DIR}/adapter.gguf"]
p = subprocess.run(full_cmd, capture_output=True, text=True)
print(f"   Done in {time.time() - t0:.2f}s: {p.stdout.strip()}")

print("3. Pushing card.json...")
subprocess.run([ADB_PATH, "push", str(CARD_PATH), f"{TARGET_DIR}/card.json"], capture_output=True)

print("4. Activating cartridge in models/adapter.gguf...")
run_adb(["shell", f"cp -f {TARGET_DIR}/adapter.gguf {MODELS_DIR}/adapter.gguf"])
run_adb(["shell", f"cp -f {TARGET_DIR}/card.json {MODELS_DIR}/card.json"])
active_cfg = json.dumps({"active": True, "build_tag": build_tag, "slug": slug, "scale": 1.0})
run_adb(["shell", f"echo '{active_cfg}' > {CONFIG_DIR}/active_cartridge.json"])

print("5. Verifying deployed files on Xiaomi Mi 10T...")
rc, out, err = run_adb(["shell", f"ls -lh {MODELS_DIR}/adapter.gguf {MODELS_DIR}/card.json {CONFIG_DIR}/active_cartridge.json"])
print(out)

print("6. Capturing screenshot via ADB...")
SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(SCREENSHOT_PATH, "wb") as f:
    subprocess.run([ADB_PATH, "exec-out", "screencap", "-p"], stdout=f)
print(f"   Saved screenshot to {SCREENSHOT_PATH} ({SCREENSHOT_PATH.stat().st_size / (1024*1024):.2f} MB)")

print("\n🎉 Deployment of LoRA Cartridge v3.0 (Tochka Plavleniya + REA) complete!")
