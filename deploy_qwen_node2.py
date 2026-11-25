import subprocess
import time
import os
import sys

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "50fb497c"

def sh(cmd):
    p = subprocess.run([ADB, "-s", DEVICE, "shell", "su", "0", "sh", "-c", cmd], capture_output=True, text=True)
    return p.stdout.strip(), p.stderr.strip()

def push_file(local_path, remote_path):
    tmp_path = f"/data/local/tmp/{os.path.basename(local_path)}"
    subprocess.run([ADB, "-s", DEVICE, "push", local_path, tmp_path], check=True, capture_output=True)
    out, err = sh(f"cp {tmp_path} {remote_path} && chown u0_a234:u0_a234 {remote_path} && chmod 755 {remote_path}")
    print(f"[OK] Pushed {local_path} -> {remote_path} (out={out}, err={err})")

print("=== 1. Checking models in Termux home ===")
out, _ = sh("ls -lh /data/data/com.termux/files/home/models/")
print(out)

print("\n=== 2. Pushing updated scripts ===")
push_file("start_reflex.sh", "/data/data/com.termux/files/home/start_reflex.sh")
push_file("download_models.sh", "/data/data/com.termux/files/home/download_models.sh")
push_file("scripts/omni_fast_router_v4_9.py", "/data/data/com.termux/files/home/omni_fast_router_v4_9.py")

print("\n=== 3. Killing previous reflex server & restarting with Qwen2.5-3B ===")
sh("pkill -9 -f 'llama-server.*8081' || true")
time.sleep(1)

# Launch start_reflex.sh via Termux environment
cmd = (
    "cd /data/data/com.termux/files/home && "
    "export HOME=/data/data/com.termux/files/home && "
    "./start_reflex.sh"
)
out, err = sh(cmd)
print("start_reflex.sh output:")
print(out)
if err:
    print("start_reflex.sh stderr:", err)

print("\n=== 4. Verifying :8081 Health & Inference ===")
healthy = False
for i in range(20):
    time.sleep(2)
    h_out, _ = sh("curl -s http://127.0.0.1:8081/health || true")
    print(f"Health ({i+1}/20): {h_out}")
    if "ok" in h_out.lower() or "ready" in h_out.lower() or "status" in h_out.lower():
        healthy = True
        break

if not healthy:
    print("reflex.log content:")
    log_out, _ = sh("cat /data/data/com.termux/files/home/reflex.log")
    print(log_out)
    sys.exit(1)

print("\n=== 5. Running Test Prompt on :8081 ===")
test_payload = '{"messages":[{"role":"user","content":"Привет! Ты кто и на каком устройстве работаешь? Ответь кратко."}],"max_tokens":100}'
test_cmd = f"curl -s -X POST http://127.0.0.1:8081/v1/chat/completions -H 'Content-Type: application/json' -d '{test_payload}'"
resp, resp_err = sh(test_cmd)
print("Inference response:")
print(resp)

print("\n=== 6. Checking Process Affinity and Status ===")
ps_out, _ = sh("ps -ef | grep -E 'llama|router'")
print(ps_out)
