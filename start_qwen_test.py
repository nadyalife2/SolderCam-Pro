import subprocess
import time

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "50fb497c"

def sh(cmd):
    p = subprocess.run([ADB, "-s", DEVICE, "shell", "su", "-c", cmd], capture_output=True, text=True)
    return p.stdout.strip(), p.stderr.strip()

print("1. Killing any existing :8081 server...")
sh("pkill -9 -f 'llama-server.*8081' || true")
time.sleep(1)

print("2. Starting Qwen2.5-3B llama-server with taskset c0 (Kryo 560 Gold A77)...")
cmd = (
    "export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib:$LD_LIBRARY_PATH; "
    "nohup taskset c0 "
    "/data/data/com.termux/files/home/llama.cpp/build/bin/llama-server "
    "-m /data/data/com.termux/files/home/models/qwen2.5-3b-instruct-q4_k_m.gguf "
    "-c 4096 -ctk q8_0 -ctv q8_0 -t 2 -np 1 --host 0.0.0.0 --port 8081 "
    "> /data/data/com.termux/files/home/reflex.log 2>&1 &"
)
sh(cmd)

print("3. Polling health...")
for i in range(15):
    time.sleep(2)
    out, _ = sh("curl -s http://127.0.0.1:8081/health || true")
    print(f"[{i+1}/15] Health: {out}")
    if "ok" in out.lower() or "ready" in out.lower() or "status" in out.lower():
        print(">>> SERVER READY! <<<")
        break
else:
    print("Log:")
    out, _ = sh("cat /data/data/com.termux/files/home/reflex.log")
    print(out)
