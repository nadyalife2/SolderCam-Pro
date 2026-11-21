import subprocess

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
remote_cmd = (
    "export PREFIX=/data/data/com.termux/files/usr; "
    "export LD_LIBRARY_PATH=/data/data/com.termux/files/home/llama.cpp/build/bin:$PREFIX/lib; "
    "/proc/10830/exe --help"
)

res = subprocess.run([adb, "shell", "su", "-mm", "0", "-c", remote_cmd], capture_output=True, text=True)
print("Return code:", res.returncode)
print("Stdout length:", len(res.stdout))
print("Stderr:", res.stderr[:200])

for line in res.stdout.splitlines():
    lower = line.lower()
    if any(k in lower for k in ["path", "public", "web", "ui", "static", "html", "host", "port"]):
        print(line)
