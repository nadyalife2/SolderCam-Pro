import subprocess, re

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
res = subprocess.run([adb, "shell", "cat", "/sdcard/ui_ready.xml"], capture_output=True, text=True, errors="ignore")
for m in re.finditer(r'<node [^>]*>', res.stdout):
    tag = m.group(0)
    if any(k in tag for k in ["custom-cloud", "Привязать", "Яндекс", "Drive", "Датасет"]):
        print(tag)
