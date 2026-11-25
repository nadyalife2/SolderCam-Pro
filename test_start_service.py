from nord_tool import su, get_nord_device
import time
import subprocess
import os

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
dev = get_nord_device()

print("1. Updating .termux/boot/start_reflex.sh...")
su("cp /data/data/com.termux/files/home/start_reflex.sh /data/data/com.termux/files/home/.termux/boot/start_reflex.sh")
su("chmod 755 /data/data/com.termux/files/home/.termux/boot/start_reflex.sh")
su("chown u0_a234:u0_a234 /data/data/com.termux/files/home/.termux/boot/start_reflex.sh")

print("2. Killing any old llama-server on 8081...")
su("pkill -9 -f 'llama-server.*8081' || true")
time.sleep(2)

print("3. Starting reflex service via start_reflex.sh...")
# Run start_reflex.sh in subshell
su("/data/data/com.termux/files/home/start_reflex.sh")
time.sleep(3)

print("4. Checking processes...")
out, _ = su("ps -ef")
for line in out.splitlines():
    if any(k in line.lower() for k in ["llama", "qwen", "bge", "router", "8081", "8082"]):
        print(line)

print("\n5. Testing 8081 Health...")
for i in range(10):
    h, _ = su("curl -s http://127.0.0.1:8081/health || true")
    print(f"Health attempt {i+1}: {h}")
    if "ok" in h.lower() or "ready" in h.lower():
        break
    time.sleep(2)

print("\n6. Testing Qwen2.5-3B local chat prompt via python urllib on device...")
py_test = """
import urllib.request, json
url = 'http://127.0.0.1:8081/v1/chat/completions'
data = {
    'messages': [
        {'role': 'user', 'content': 'Привет! Назови себя и свой процессор.'}
    ],
    'max_tokens': 60
}
req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode())
        print('SUCCESS:', res['choices'][0]['message']['content'])
except Exception as e:
    print('ERROR:', e)
"""
# Save on device and execute with python3
su(f"cat << 'EOF' > /data/data/com.termux/files/home/test_infer.py\n{py_test}\nEOF")
out, err = su("/data/data/com.termux/files/usr/bin/python3 /data/data/com.termux/files/home/test_infer.py")
print("Inference output:")
print(out)
if err:
    print("Inference err:", err)
