# -*- coding: utf-8 -*-
import subprocess
import time

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"

print("Waiting for device...")
while True:
    r = subprocess.run([ADB, "devices"], capture_output=True, text=True, errors="replace")
    if "\tdevice" in r.stdout:
        print("Device connected!")
        break
    time.sleep(0.3)

# Dump crash buffer
crash = subprocess.run([ADB, "shell", "logcat -b crash -d"], capture_output=True, text=True, errors="replace").stdout
print("=== CRASH BUFFER ===")
print(crash[:2000])

# Dump system server errors
errs = subprocess.run([ADB, "shell", "logcat -d | grep -iE 'AndroidRuntime.*FATAL|SystemServer.*crash|RescueParty' | tail -n 20"], capture_output=True, text=True, errors="replace").stdout
print("=== SYSTEM ERRORS ===")
print(errs)
