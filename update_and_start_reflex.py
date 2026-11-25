import subprocess
import time
import os
import sys

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "50fb497c"

def su(cmd):
    p = subprocess.run([ADB, "-s", DEVICE, "shell", f"su -c '{cmd}'"], capture_output=True, text=True)
    return p.stdout.strip(), p.stderr.strip()

def push_and_install(local_path, remote_path):
    fname = os.path.basename(local_path)
    tmp_path = f"/data/local/tmp/{fname}"
    subprocess.run([ADB, "-s", DEVICE, "push", local_path, tmp_path], check=True, capture_output=True)
    su(f"cp {tmp_path} {remote_path}")
    su(f"chown u0_a234:u0_a234 {remote_path}")
    su(f"chmod 755 {remote_path}")
    print(f"[OK] Installed {local_path} -> {remote_path}")

print("=== 1. Models Verification ===")
out, _ = su("ls -lh /data/data/com.termux/files/home/models/")
print(out)

print("\n=== 2. Installing Updated Scripts ===")
push_and_install("start_reflex.sh", "/data/data/com.termux/files/home/start_reflex.sh")
push_and_install("download_models.sh", "/data/data/com.termux/files/home/download_models.sh")
push_and_install("scripts/omni_fast_router_v4_9.py", "/data/data/com.termux/files/home/omni_fast_router_v4_9.py")

print("\n=== 3. Restarting Services via start_reflex.sh ===")
# Stop old reflex server and router
su("pkill -9 -f 'llama-server.*8081' || true")
su("pkill -9 -f 'omni_fast_router_v4_9.py' || true")
time.sleep(1)

# Execute start_reflex.sh
out, err = su("sh /data/data/com.termux/files/home/start_reflex.sh")
print("start_reflex.sh output:")
print(out)
if err:
    print("start_reflex.sh err:", err)

print("\n=== 4. Waiting for Qwen2.5-3B on :8081 ===")
healthy = False
for i in range(25):
    time.sleep(2)
    h_out, _ = su("curl -s http://127.0.0.1:8081/health || true")
    print(f"Health ({i+1}/25): {h_out}")
    if "ok" in h_out.lower() or "ready" in h_out.lower() or "status" in h_out.lower():
        healthy = True
        break

if not healthy:
    print("Failed to start reflex server. Checking reflex.log:")
    log_out, _ = su("cat /data/data/com.termux/files/home/reflex.log")
    print(log_out)
    sys.exit(1)

print("\n=== 5. Running Real LLM Test on :8081 ===")
test_json = '{\\"messages\\":[{\\"role\\":\\"user\\",\\"content\\":\\"Напиши одно предложение: кто ты и на каком чипе работаешь.\\"}],\\"max_tokens\\":60}'
out_llm, err_llm = su(f"curl -s -X POST http://127.0.0.1:8081/v1/chat/completions -H 'Content-Type: application/json' -d '{test_json}'")
print("Response from Qwen2.5-3B-Instruct:")
print(out_llm)

print("\n=== 6. Checking Fast-Path Router on :8080 / :8000 ===")
for i in range(10):
    time.sleep(1)
    r_out, _ = su("curl -s http://127.0.0.1:8080/api/cluster_status || true")
    if r_out:
        print("Router status output:")
        print(r_out[:300])
        break
