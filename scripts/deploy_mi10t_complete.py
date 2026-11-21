#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full deployment to Xiaomi Mi 10T 5G (Node-1 Brain):
1. Sets permanent Wireless ADB (persist.adb.tcp.port 5555).
2. Deploys updated start_brain.sh with dynamic LoRA mounting.
3. Deploys clean_termux_pristine.sh.
4. Deploys omni_knowledge.db (46 articles).
5. Launches start_brain.sh and verifies port 8080.
6. Takes proof screenshot via ADB.
"""

import subprocess
import time
from pathlib import Path

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
TARGET = "192.168.31.161:5555"

def run_adb(args):
    cmd = [ADB, "-s", TARGET] + args
    return subprocess.run(cmd, capture_output=True, text=True)

def deploy():
    print(f"🚀 [Mi 10T 5G] Starting full deployment to {TARGET}...")

    # 1. Enable persistent ADB Wi-Fi
    run_adb(["shell", "su -c 'setprop persist.adb.tcp.port 5555; setprop service.adb.tcp.port 5555'"])
    print("📶 [1/5] Persistent ADB Wi-Fi port 5555 configured.")

    # 2. Push clean_termux_pristine.sh
    clean_sh = Path("scripts/clean_termux_pristine.sh")
    run_adb(["push", str(clean_sh), "/sdcard/clean_termux_pristine.sh"])
    run_adb(["shell", "su -c 'cp -f /sdcard/clean_termux_pristine.sh /data/data/com.termux/files/home/clean_termux_pristine.sh && chmod +x /data/data/com.termux/files/home/clean_termux_pristine.sh'"])
    print("🧹 [2/5] clean_termux_pristine.sh deployed to Termux.")

    # 3. Push omni_knowledge.db
    kb_path = Path("datasets/omni_knowledge.db")
    run_adb(["push", str(kb_path), "/sdcard/omni_knowledge.db"])
    run_adb(["shell", "su -c 'cp -f /sdcard/omni_knowledge.db /data/data/com.termux/files/home/omni_knowledge.db'"])
    print("📚 [3/5] omni_knowledge.db (46 articles) deployed.")

    # 4. Create and deploy start_brain.sh
    start_brain_content = """#!/data/data/com.termux/files/usr/bin/bash
export HOME="/data/data/com.termux/files/home"
export PREFIX="/data/data/com.termux/files/usr"
export PATH="$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="/data/data/com.termux/files/home/llama.cpp/build/bin:$PREFIX/lib"
export OMP_NUM_THREADS=4
export GGML_OPENMP=1

echo omni_brain > /sys/power/wake_lock 2>/dev/null
iw dev wlan0 set power_save off 2>/dev/null

# Daemons
pgrep sshd >/dev/null || $PREFIX/bin/sshd
pgrep -f battery_guard_24x7.sh >/dev/null || nohup "$HOME/battery_guard_24x7.sh" >/dev/null 2>&1 &
pgrep -f thermal_guard.sh >/dev/null || nohup "$HOME/thermal_guard.sh" >/dev/null 2>&1 &
pgrep -f node_telemetry.sh >/dev/null || nohup "$HOME/node_telemetry.sh" >/dev/null 2>&1 &

MODEL_FILE="$HOME/models/brain.gguf"
ADAPTER_FILE="$HOME/models/adapter.gguf"
LLAMA="$HOME/llama.cpp/build/bin/llama-server"

killall -9 llama-server 2>/dev/null
sleep 1

LORA_FLAG=""
if [ -f "$ADAPTER_FILE" ]; then
    LORA_FLAG="--lora $ADAPTER_FILE"
fi

# Master Blueprint Launch v5.2:
nohup taskset -c 4,5,6,7 "$LLAMA" \\
  -m "$MODEL_FILE" \\
  $LORA_FLAG \\
  --host 0.0.0.0 --port 8080 \\
  --path "$HOME/web_ui" \\
  -np 1 \\
  -t 4 -tb 4 \\
  -c 4096 \\
  -b 256 -ub 64 \\
  -ctk f16 -ctv f16 \\
  --swa-full \\
  -lcd "$HOME/lookup.cache" \\
  --cache-reuse 256 > "$HOME/brain.log" 2>&1 &

echo "Triad-Omni Brain v5.2 launched with active LoRA on port 8080!"
"""
    tmp_sh = Path("scripts/start_brain_v5_2.sh")
    tmp_sh.write_text(start_brain_content, encoding="utf-8")
    run_adb(["push", str(tmp_sh), "/sdcard/start_brain.sh"])
    run_adb(["shell", "su -c 'cp -f /sdcard/start_brain.sh /data/data/com.termux/files/home/start_brain.sh && chmod +x /data/data/com.termux/files/home/start_brain.sh'"])
    print("🧠 [4/5] start_brain.sh with dynamic LoRA mounting deployed.")

    # 5. Launch start_brain.sh
    print("⚡ [5/5] Launching start_brain.sh on Mi 10T 5G (Snapdragon 865)...")
    run_adb(["shell", "su -c 'bash /data/data/com.termux/files/home/start_brain.sh'"])

    # Wait for startup
    time.sleep(3)
    p = run_adb(["shell", "su -c 'ps -ef | grep llama-server'"])
    print("Processes on Mi 10T:\n", p.stdout.strip())

    # Check brain.log
    l = run_adb(["shell", "su -c 'tail -n 15 /data/data/com.termux/files/home/brain.log'"])
    print("Brain log tail:\n", l.stdout.strip())

    # Screenshot
    scr_path = Path("screenshots/mi10t_brain_lora_deployed.png")
    scr_path.parent.mkdir(parents=True, exist_ok=True)
    with open(scr_path, "wb") as f:
        subprocess.run([ADB, "-s", TARGET, "exec-out", "screencap", "-p"], stdout=f)
    print(f"📸 Screenshot saved: {scr_path}")

if __name__ == "__main__":
    deploy()
