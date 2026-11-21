# -*- coding: utf-8 -*-
import subprocess

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "50fb497c"

PACKAGES = [
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

for p in PACKAGES:
    res = subprocess.run([ADB, "-s", DEVICE, "shell", f"cmd package install-existing {p}"], capture_output=True, text=True, errors="replace")
    print(f"[{p}]: {res.stdout.strip()}")

anim = subprocess.run([ADB, "-s", DEVICE, "shell", "getprop init.svc.bootanim"], capture_output=True, text=True, errors="replace").stdout.strip()
boot = subprocess.run([ADB, "-s", DEVICE, "shell", "getprop sys.boot_completed"], capture_output=True, text=True, errors="replace").stdout.strip()
print(f"bootanim: {anim} | boot_completed: {boot}")
