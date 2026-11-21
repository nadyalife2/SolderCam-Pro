# -*- coding: utf-8 -*-
import subprocess
import json
import time

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "50fb497c"

def run_adb(cmd):
    full_cmd = [ADB, "-s", DEVICE] + cmd
    res = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return res.stdout.strip()

PACKAGES_STAGE2 = [
    "com.google.android.apps.maps",
    "com.google.android.apps.docs",
    "com.google.android.apps.docs.editors.docs",
    "com.google.android.apps.photos",
    "cn.oneplus.photos",
    "com.google.android.apps.nbu.files",
    "net.oneplus.weather",
    "com.oneplus.wallpaper",
    "net.oneplus.wallpaperresources",
    "com.android.wallpaper.livepicker",
    "com.oneplus.faceunlock",
    "com.oneplus.note",
    "com.oneplus.soundrecorder",
    "net.oneplus.widget",
    "com.oneplus.canvasresources",
    "com.google.android.apps.cloudprint",
    "com.google.android.contactkeys",
    "com.google.android.safetycore",
    "com.google.android.as"  # Android System Intelligence (100MB+ in background)
]

backup_file = r"d:\для one plus nord n10\heavy_debloat_removed_packages.json"
try:
    with open(backup_file, "r", encoding="utf-8") as f:
        existing = json.load(f)
except Exception:
    existing = []

removed_now = []
for pkg in PACKAGES_STAGE2:
    res = run_adb(["shell", f"pm uninstall -k --user 0 {pkg}"])
    if "Success" in res:
        removed_now.append(pkg)
        if pkg not in existing:
            existing.append(pkg)
        print(f"[-] Удален: {pkg}")
    else:
        print(f"[!] Пропуск {pkg}: {res}")

with open(backup_file, "w", encoding="utf-8") as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)

print(f"\nВсего в резервном манифесте: {len(existing)} пакетов.")
print("Отправка команды перезагрузки (adb reboot)...")
run_adb(["reboot"])
print("Смартфон отправлен в перезагрузку!")
