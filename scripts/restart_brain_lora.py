import subprocess
import time

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
target = "192.168.31.161:5555"

# Chown and execute
cmd = [adb, "-s", target, "shell", "su -c 'chown -R u0_a212:u0_a212 /data/data/com.termux/files/home'"]
subprocess.run(cmd, check=True)

# Kill old llama-server
cmd_kill = [adb, "-s", target, "shell", "su -c 'pkill -9 -f llama-server'"]
subprocess.run(cmd_kill)
time.sleep(1)

# Start new brain with LoRA
cmd_start = [adb, "-s", target, "shell", "su u0_a212 -c '/data/data/com.termux/files/usr/bin/bash /data/data/com.termux/files/home/start_brain.sh'"]
res = subprocess.run(cmd_start, capture_output=True, text=True)
print("Start output:", res.stdout.strip())

time.sleep(3)
cmd_ps = [adb, "-s", target, "shell", "su -c 'ps -ef | grep llama-server'"]
res_ps = subprocess.run(cmd_ps, capture_output=True, text=True)
print("Processes:\n", res_ps.stdout.strip())

cmd_log = [adb, "-s", target, "shell", "su -c 'tail -n 25 /data/data/com.termux/files/home/brain.log'"]
res_log = subprocess.run(cmd_log, capture_output=True, text=True)
print("Brain log tail:\n", res_log.stdout.strip())
