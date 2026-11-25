import subprocess
import os

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def get_nord_device():
    res = subprocess.run([ADB, "devices"], capture_output=True, text=True)
    devices = [line.split()[0] for line in res.stdout.strip().splitlines()[1:] if "\tdevice" in line]
    if "50fb497c" in devices:
        return "50fb497c"
    if "192.168.31.57:5555" in devices:
        return "192.168.31.57:5555"
    for d in devices:
        p = subprocess.run([ADB, "-s", d, "shell", "getprop", "ro.product.device"], capture_output=True, text=True)
        if "billie" in p.stdout.lower() or "n10" in p.stdout.lower():
            return d
    raise RuntimeError("OnePlus Nord N10 not found in adb devices!")

def su(cmd):
    dev = get_nord_device()
    res = subprocess.run([ADB, "-s", dev, "shell", "su", "-c", cmd], capture_output=True, text=True)
    return res.stdout.strip(), res.stderr.strip()

if __name__ == "__main__":
    dev = get_nord_device()
    print("Detected Nord device:", dev)
    out, err = su("ps -ef")
    for line in out.splitlines():
        if any(k in line.lower() for k in ["llama", "router", "bge", "python", "qwen"]):
            print(line)
