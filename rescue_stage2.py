# -*- coding: utf-8 -*-
import subprocess
import time
import sys

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"

PACKAGES_TO_RESTORE = [
    "com.google.android.as",
    "com.oneplus.wallpaper",
    "net.oneplus.wallpaperresources",
    "com.android.wallpaper.livepicker",
    "com.oneplus.faceunlock",
    "com.google.android.apps.nbu.files",
    "com.google.android.apps.photos",
    "com.google.android.apps.maps",
    "com.google.android.apps.docs",
    "com.google.android.apps.docs.editors.docs",
    "net.oneplus.weather",
    "com.oneplus.note",
    "com.oneplus.soundrecorder",
    "net.oneplus.widget",
    "com.oneplus.canvasresources",
    "com.google.android.apps.cloudprint",
    "com.google.android.contactkeys",
    "com.google.android.safetycore"
]

print("=== ЗАПУСК СЛУЖБЫ СПАСЕНИЯ И ВОССТАНОВЛЕНИЯ STAGE 2 ===")
print("Ожидание появления устройства по ADB...")

def check_device():
    res = subprocess.run([ADB, "devices"], capture_output=True, text=True, errors="replace")
    for line in res.stdout.splitlines():
        if "\tdevice" in line:
            return line.split("\t")[0]
    return None

dev = None
while not dev:
    dev = check_device()
    if dev:
        print(f"[+] Устройство обнаружено: {dev}!")
        break
    time.sleep(0.5)

print("\n[+] Мгновенное восстановление системных пакетов...")
for pkg in PACKAGES_TO_RESTORE:
    cmd = [ADB, "-s", dev, "shell", f"cmd package install-existing {pkg}"]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    out = r.stdout.strip()
    print(f"[{pkg}]: {out}")

print("\nПроверка статуса bootanim...")
anim = subprocess.run([ADB, "-s", dev, "shell", "getprop init.svc.bootanim"], capture_output=True, text=True, errors="replace").stdout.strip()
print(f"Статус bootanim: {anim}")

print("=== ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО ===")
