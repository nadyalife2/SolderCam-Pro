import subprocess
import re

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
cmd = [adb, "exec-out", "su", "-c", "head -c 4096 /data/data/com.termux/files/home/models/brain.gguf"]
p = subprocess.run(cmd, capture_output=True)
data = p.stdout
print(f"Read {len(data)} bytes from brain.gguf header")

matches = re.findall(rb'[\x20-\x7e]{3,}', data)
print("Strings in brain.gguf:")
for m in matches[:40]:
    print(" ", m.decode())
