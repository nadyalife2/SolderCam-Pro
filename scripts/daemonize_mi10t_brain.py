import subprocess
import time

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
target = "192.168.31.161:5555"

# Launch in background via nohup
daemon_cmd = (
    "export HOME=/data/data/com.termux/files/home; "
    "export PREFIX=/data/data/com.termux/files/usr; "
    "export PATH=$PREFIX/bin:$PATH; "
    "export LD_LIBRARY_PATH=/data/data/com.termux/files/home/llama.cpp/build/bin:$PREFIX/lib; "
    "export OMP_NUM_THREADS=4; "
    "export GGML_OPENMP=1; "
    "nohup taskset -c 4,5,6,7 /data/data/com.termux/files/home/llama.cpp/build/bin/llama-server "
    "-m /data/data/com.termux/files/home/models/brain.gguf "
    "--lora /data/data/com.termux/files/home/models/adapter.gguf "
    "--host 0.0.0.0 --port 8080 "
    "-np 1 -t 4 -tb 4 -c 4096 -b 256 -ub 64 -ctk f16 -ctv f16 --swa-full "
    "-lcd /data/data/com.termux/files/home/lookup.cache "
    "> /data/data/com.termux/files/home/brain.log 2>&1 &"
)

cmd = [adb, "-s", target, "shell", f"su u0_a212 -c '{daemon_cmd}'"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("Daemon launched. Status:", res.returncode)

time.sleep(3)
cmd_ps = [adb, "-s", target, "shell", "su -c 'ps -ef | grep llama-server'"]
res_ps = subprocess.run(cmd_ps, capture_output=True, text=True)
print("Processes:\n", res_ps.stdout.strip())
