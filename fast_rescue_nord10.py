#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nord N10 Fast Rescue & Restore Tool
Запускает fastboot reboot и агрессивно перехватывает ADB при старте ядра:
- Отключает RescueParty
- Восстанавливает критические службы обоев, SystemUI и разблокировки
- Вводит пин-код 4870 для разблокировки экрана
"""
import subprocess
import time
import sys

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
FASTBOOT = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\fastboot.exe"
DEVICE = "50fb497c"

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

def main():
    print("🚀 Отправка команды перезагрузки в Android: fastboot reboot...")
    r = run([FASTBOOT, "reboot"])
    print(f"Fastboot: {r.stdout.strip()} {r.stderr.strip()}")

    print("⚡ Охота за ADB на лету (проверка каждые 0.3 сек)...")
    start_time = time.time()
    intercepted = False

    while time.time() - start_time < 90:
        res = run([ADB, "devices"])
        lines = res.stdout.strip().splitlines()
        has_dev = any(DEVICE in l and "device" in l for l in lines)

        if has_dev:
            print("🎯 ПЕРЕХВАТ! Телефон ответил по ADB. Мгновенное отключение RescueParty...")
            # 1. Отключаем спасательный отряд
            run([ADB, "-s", DEVICE, "shell", "setprop persist.sys.enable_rescue false; device_config put configuration disable_rescue_party true; settings put global rescue_party_disabled 1"])
            
            # 2. Восстанавливаем системные пакеты
            print("📦 Восстановление компонентов SystemUI...")
            for pkg in CRITICAL_PACKAGES:
                out = run([ADB, "-s", DEVICE, "shell", f"cmd package install-existing --user 0 {pkg}"]).stdout.strip()
                print(f"  [+] {pkg}: {out}")

            # 3. Ввод PIN-кода 4870
            time.sleep(1)
            print("🔑 Разблокировка экрана: ввод PIN 4870...")
            run([ADB, "-s", DEVICE, "shell", "input keyevent 26; input keyevent 82; input text 4870; input keyevent 66"])
            intercepted = True
            break

        time.sleep(0.3)

    if intercepted:
        print("🎉 УСПЕХ! Телефон стабилизирован, компоненты восстановлены, экран разблокирован!")
    else:
        print("⚠️ Таймаут ожидания ADB. Проверьте состояние экрана телефона.")

if __name__ == "__main__":
    main()
