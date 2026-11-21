import sys, subprocess
from pathlib import Path

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
out_name = sys.argv[1] if len(sys.argv) > 1 else "screenshots/latest.png"
out_path = Path(out_name)
out_path.parent.mkdir(parents=True, exist_ok=True)

raw = subprocess.check_output([adb, "exec-out", "screencap", "-p"])
with open(out_path, "wb") as f:
    f.write(raw)
print(f"Captured {len(raw)} bytes to {out_path}")
