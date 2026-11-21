import subprocess

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
cmd = [adb, "shell", "su -c '/data/data/com.termux/files/usr/bin/bash -c \"export PATH=/data/data/com.termux/files/usr/bin:\$PATH; export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib; /data/data/com.termux/files/home/llama.cpp/build/bin/llama-server --help 2>&1\"'"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("rc:", res.returncode)
print("stdout:", res.stdout)
print("stderr:", res.stderr)
