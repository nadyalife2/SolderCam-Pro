import subprocess

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
device = "5fcca09"

cmd = (
    "grep -q 'dport 5000' /data/data/com.termux/files/home/start_brain.sh || "
    "sed -i '/to-port 8080/a iptables -t nat -A OUTPUT -p tcp -d 127.0.0.1 --dport 5000 -j REDIRECT --to-port 8080 2>/dev/null' /data/data/com.termux/files/home/start_brain.sh"
)

res = subprocess.run([adb, "-s", device, "shell", f"su -c \"{cmd}\""], capture_output=True, text=True)
print("Result:", res.returncode, res.stdout, res.stderr)

check = subprocess.run([adb, "-s", device, "shell", "su -c 'cat /data/data/com.termux/files/home/start_brain.sh | grep -E \"iptables|8080|5000\"'"], capture_output=True, text=True)
print("Verified script lines:\n", check.stdout)
