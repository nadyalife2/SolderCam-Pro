import subprocess

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
cmd = [adb, "-s", "5fcca09", "shell", "su -c 'export LD_LIBRARY_PATH=/data/data/com.termux/files/home/llama.cpp/build/bin:/data/data/com.termux/files/usr/lib; /data/data/com.termux/files/home/llama.cpp/build/bin/llama-server --help'"]
res = subprocess.run(cmd, capture_output=True, text=True)
found = False
for line in res.stdout.splitlines():
    if "lora" in line.lower() or "adapter" in line.lower():
        print(line)
        found = True
if not found:
    print("No lora lines found. Total lines:", len(res.stdout.splitlines()))
