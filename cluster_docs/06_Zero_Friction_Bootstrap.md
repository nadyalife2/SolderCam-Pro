# 06. Zero-Friction Bootstrap: Авто-Раскатка Узлов и Zeroconf (mDNS)

> Цель: подключение нового смартфона-донора за **1 клик** через USB без ручного ввода команд в консоли Termux и автоматическое обнаружение узлов в сети без жестко захардкоженных IP-адресов.

---

## 1. Автоматическое обнаружение через Zeroconf (mDNS)

Шлюз на Redmi Note 4 автоматически анонсирует себя в локальной сети по протоколу mDNS / DNS-SD (`_omni._tcp.local.`, порт 8000, имя хоста `omni-hub.local`).

### Преимущества чистой Python-реализации:
- Не зависит от системного демона `mdnsd` Android.
- Продолжает работать даже после выполнения `stop zygote && stop surfaceflinger`.
- ПК на Linux (Avahi) и macOS резолвят адрес `http://omni-hub.local:8000` нативно.
- На Windows для работы mDNS достаточно службы Bonjour (ставится с iTunes) или прямого вызова DNS-SD.

Шлюз (`omni_gateway.py`) включает встроенный блок zeroconf:
```python
try:
    from zeroconf import Zeroconf, ServiceInfo
    ip_bytes = socket.inet_aton(MY_IP)
    info = ServiceInfo(
        "_omni._tcp.local.",
        "OmniGateway._omni._tcp.local.",
        addresses=[ip_bytes],
        port=PORT,
        server="omni-hub.local.",
        properties={"version": "4.7", "role": "gateway"}
    )
    zc = Zeroconf()
    zc.register_service(info)
except ImportError:
    pass
```

---

## 2. Скрипт автоматического подключения смартфона `bootstrap_node.py`

Скрипт запускается на ПК (Windows или Linux), когда новый телефон подключен по USB с включенной отладкой по ADB.

### 2.1. Полный код `bootstrap_node.py`

Создайте на ПК файл `~/omni_auto_trainer/bootstrap_node.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Zero-Friction Bootstrap (ПК -> Смартфон по ADB)
Использование: python bootstrap_node.py [mi10t | nord10 | note4]
"""
import sys
import os
import time
import subprocess

ROLE = sys.argv[1] if len(sys.argv) > 1 else "mi10t"
H = "/data/data/com.termux/files/home"
APK_DIR = os.path.expanduser("~/omni_apks")

def run(cmd, check=True):
    return subprocess.run(cmd, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def adb(*args):
    r = run(["adb", *args])
    return r.stdout.strip()

def su(cmd):
    return adb("shell", "su", "-c", cmd)

def main():
    print(f"🚀 Запуск бутстрапа узла с ролью [{ROLE}]...")

    # 1. Проверка ADB-соединения
    devices = adb("devices")
    if "device\n" not in devices and not devices.endswith("device"):
        print("❌ Устройство не найдено по ADB. Проверьте кабель и отладку по USB.")
        sys.exit(1)

    print("✅ Устройство подключено.")

    # 2. Отключение Android 12-15 Phantom Process Killer
    print("🔧 Отключение Phantom Process Killer и Doze ограничения...")
    try:
        adb("shell", "/system/bin/device_config", "put", "activity_manager", "max_phantom_processes", "2147483647")
        adb("shell", "setprop", "persist.sys.fflag.override.settings_enable_monitor_phantom_procs", "false")
    except Exception as e:
        print(f"  (Предупреждение по device_config: {e})")

    # 3. Установка Termux, Termux:Boot, Termux:API
    print("📦 Установка Termux APK...")
    for apk in ("termux.apk", "termux-boot.apk", "termux-api.apk"):
        path = os.path.join(APK_DIR, apk)
        if os.path.exists(path):
            adb("push", path, f"/data/local/tmp/{apk}")
            try:
                su(f"pm install -r /data/local/tmp/{apk}")
            except Exception:
                adb("install", "-r", path)

    # 4. Первый запуск Termux для генерации /data/data/com.termux/files/home
    print("⏳ Инициализация окружения Termux (10 сек)...")
    adb("shell", "monkey", "-p", "com.termux", "1")
    time.sleep(10)

    # 5. Определение UID Termux
    uid_str = adb("shell", "stat", "-c", "%u", "/data/data/com.termux")
    uid = uid_str.strip()
    if not uid.isdigit():
        uid = "10150"  # fallback
    print(f"🔑 Обнаружен Termux UID: {uid}")

    # 6. Создание служебных папок
    su(f"mkdir -p {H}/.termux {H}/.ssh {H}/.termux/boot")

    # 7. Конфигурация Termux и SSH
    print("📄 Настройка termux.properties и authorized_keys...")
    ak_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    if os.path.exists(ak_path):
        adb("push", ak_path, "/data/local/tmp/ak")
        su(f"cp /data/local/tmp/ak {H}/.ssh/authorized_keys")
        su(f"chmod 600 {H}/.ssh/authorized_keys")

    su(f"echo allow-external-apps=true > {H}/.termux/termux.properties")

    # 8. Копирование роли узла
    role_script = f"node_bootstrap_{ROLE}.sh"
    if os.path.exists(role_script):
        adb("push", role_script, "/data/local/tmp/node_bootstrap.sh")
        su(f"cp /data/local/tmp/node_bootstrap.sh {H}/bootstrap.sh")
        su(f"chmod +x {H}/bootstrap.sh")

    # 9. КРИТИЧНО: chown UID и восстановление контекста SELinux
    print("🔒 Восстановление прав chown и SELinux context...")
    su(f"chown -R {uid}:{uid} {H}")
    su("restorecon -R -F /data/data/com.termux/files")

    # 10. Белый список Doze
    print("⚡ Отключение энергосбережения Doze...")
    adb("shell", "dumpsys", "deviceidle", "whitelist", "+com.termux")
    adb("shell", "dumpsys", "deviceidle", "whitelist", "+com.termux.boot")

    # 11. Запуск bootstrap-скрипта через RunCommandService
    print("🚀 Старт bootstrap.sh через Termux RunCommandService...")
    adb("shell", "am", "start-foreground-service", "-n", "com.termux/.app.RunCommandService",
        "-a", "com.termux.RUN_COMMAND",
        "--es", "com.termux.RUN_COMMAND_PATH", "/data/data/com.termux/files/usr/bin/bash",
        "--es", "com.termux.RUN_COMMAND_ARGUMENTS", f"{H}/bootstrap.sh")

    print(f"🎉 Узел [{ROLE}] успешно сконфигурирован и развернут!")

if __name__ == "__main__":
    main()
```

---

## 3. Скрипт роли смартфона `node_bootstrap_mi10t.sh`

Данный скрипт автоматически выполняется внутри Termux на Mi 10T после первого подключения:

```sh
#!/data/data/com.termux/files/usr/bin/sh
pkg update -y
pkg install -y git cmake ninja openssh curl iw rsync python
sshd
termux-wake-lock
echo "omni_brain" > /sys/power/wake_lock 2>/dev/null
echo "0" > /sys/class/leds/lcd-backlight/brightness 2>/dev/null

# Скачивание репозитория кластера
cd ~
git clone --depth 1 https://github.com/ggml-org/llama.cpp
cd llama.cpp && cmake -B build -G Ninja -DGGML_OPENMP=OFF -DGGML_RPC=OFF && cmake --build build -j6

echo "✅ Инициализация Mi 10T завершена."
```

---

## 4. Памятка по безопасности и тонкостям Android
1. **Root-доступ**: при первом вызове `su` на экране телефона появится диалог Magisk / KernelSU / APatch — нажмите **«Предоставить навсегда»**.
2. **Без Root**: потребуется ровно один ручной тап по иконке Termux на экране телефона для первичной инициализации окружения.
3. **Запрет убийства процессов**: на MIUI / HyperOS дополнительно зайдите в настройки приложения Termux -> **Контроль активности: «Нет ограничений»** и включите **«Автозапуск»**.
