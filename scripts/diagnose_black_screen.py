import subprocess
import sys
from pathlib import Path

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "5fcca09"

def run_adb(args):
    cmd = [ADB, "-s", DEVICE] + args
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return res.stdout.strip()

print("1. Capturing screenshot...")
run_adb(["shell", "screencap", "-p", "/sdcard/black_screen_now.png"])
pull_res = run_adb(["pull", "/sdcard/black_screen_now.png", r"d:\для one plus nord n10\screenshots\mi10t_black_screen_diagnose.png"])
print(f"Screenshot pull: {pull_res}")

print("\n2. Checking Current Focused Window/App...")
focus = run_adb(["shell", "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'"])
print(focus)

print("\n3. Checking Listening Ports on Device...")
ports = run_adb(["shell", "su -c 'netstat -tuln 2>/dev/null || ss -tuln 2>/dev/null'"])
print(ports)

print("\n4. Checking Background Daemons & Servers...")
procs = run_adb(["shell", "su -c 'ps -ef | grep -E \"llama|router|termux|python|brain|omni|solder\" | grep -v grep'"])
print(procs if procs else "No matching processes found!")

print("\n5. Checking Termux brain.log...")
log = run_adb(["shell", "su -c 'tail -n 25 /data/data/com.termux/files/home/brain.log 2>/dev/null'"])
print(log if log else "brain.log empty or missing!")

print("\n6. Checking Termux router.log...")
rlog = run_adb(["shell", "su -c 'tail -n 25 /data/data/com.termux/files/home/router.log 2>/dev/null'"])
print(rlog if rlog else "router.log empty or missing!")
