#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nord N10 Rescue & Restore Script
Восстанавливает отключенные системные пакеты OnePlus через pm install-existing,
отключает RescueParty и возвращает систему в рабочий режим.
"""
import subprocess
import time
import os
import sys

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
FASTBOOT = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\fastboot.exe"
DEVICE = "50fb497c"

# Критические системные пакеты OnePlus, без которых SystemUI падает в RescueParty:
CRITICAL_PACKAGES = [
    "com.oneplus.wallpaper",
    "net.oneplus.wallpaperresources",
    "com.android.wallpaper.livepicker",
    "com.oneplus.canvasresources",
    "com.oneplus.faceunlock",
    "net.oneplus.widget",
    "com.oneplus.brickmode",
    "cn.oneplus.photos",
    "net.oneplus.odm.provider",
    "com.oneplus.account",
    "com.oneplus.gamespace",
    "com.google.android.safetycore"
]

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

def adb_shell(cmd_str):
    return run([ADB, "-s", DEVICE, "shell", cmd_str]).stdout.strip()

def restore_critical():
    print("🚑 Отключение сторожевого пса RescueParty...")
    adb_shell("setprop persist.sys.enable_rescue false")
    adb_shell("device_config put configuration disable_rescue_party true")
    adb_shell("settings put global rescue_party_disabled 1")

    print(f"📦 Восстановление {len(CRITICAL_PACKAGES)} критических компонентов OnePlus...")
    for pkg in CRITICAL_PACKAGES:
        res = adb_shell(f"cmd package install-existing --user 0 {pkg}")
        if "installed for user" in res or "Success" in res:
            print(f"  [+] Восстановлен: {pkg}")
        else:
            print(f"  [~] {pkg}: {res}")

    print("🎉 Критические пакеты восстановлены! Теперь SystemUI и локскрин не упадут.")

def main():
    print("⏳ Ожидание появления смартфона по ADB...")
    while True:
        r = run([ADB, "devices"])
        if DEVICE in r.stdout and "device" in r.stdout:
            print(f"✅ Обнаружен {DEVICE} в режиме ADB!")
            restore_critical()
            break
        time.sleep(1)

if __name__ == "__main__":
    main()
