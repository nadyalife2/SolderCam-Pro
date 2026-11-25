import subprocess
import os

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "50fb497c"

def sh(cmd):
    res = subprocess.run([ADB, "-s", DEVICE, "shell", "su", "-c", cmd], capture_output=True, text=True)
    return res.stdout.strip(), res.stderr.strip()

print("=== PS ===")
out, err = sh("ps -ef")
for line in out.splitlines():
    if any(k in line.lower() for k in ["llama", "bge", "server", "python", "proot", "808", "alpine"]):
        print(line)

print("\n=== Storage ===")
out, _ = sh("df -h /data /sdcard")
print(out)

print("\n=== Checking /data/local/tmp ===")
out, _ = sh("ls -la /data/local/tmp")
print(out)

print("\n=== Checking Termux Home ===")
out, _ = sh("ls -la /data/data/com.termux/files/home 2>/dev/null")
print(out)

print("\n=== Netstat / Open Ports ===")
out, _ = sh("netstat -tuln 2>/dev/null || ss -tuln 2>/dev/null")
print(out)
