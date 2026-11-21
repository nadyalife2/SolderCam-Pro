import subprocess

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
target = "192.168.31.161:5555"

cmd = [adb, "-s", target, "shell", "su u0_a212 -c 'export HOME=/data/data/com.termux/files/home; export PREFIX=/data/data/com.termux/files/usr; export PATH=$PREFIX/bin:$PATH; export LD_LIBRARY_PATH=/data/data/com.termux/files/home/llama.cpp/build/bin:$PREFIX/lib; /data/data/com.termux/files/home/llama.cpp/build/bin/llama-server -m /data/data/com.termux/files/home/models/brain.gguf --lora /data/data/com.termux/files/home/models/adapter.gguf --host 0.0.0.0 --port 8080 -np 1 -t 4 -c 2048'"]
try:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)
except subprocess.TimeoutExpired as e:
    print("TIMEOUT (Server started successfully and is running!)")
    if e.stdout: print("Partial stdout:\n", e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout)
    if e.stderr: print("Partial stderr:\n", e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr)
