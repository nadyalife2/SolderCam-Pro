import sys, subprocess, os
from pathlib import Path

adb = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
if not os.path.exists(adb):
    adb = "adb"

out_name = "screenshots/latest.png"
device_serial = None

args = sys.argv[1:]
if len(args) > 0 and args[0] == "-s" and len(args) > 1:
    device_serial = args[1]
    args = args[2:]
if len(args) > 0:
    out_name = args[0]

# Auto-detect device if multiple devices attached
if not device_serial:
    try:
        dev_out = subprocess.check_output([adb, "devices"], text=True)
        lines = [l.split()[0] for l in dev_out.splitlines()[1:] if l.strip() and "device" in l]
        if lines:
            # Prefer USB over Wi-Fi
            usb_devs = [d for d in lines if ":" not in d]
            device_serial = usb_devs[0] if usb_devs else lines[0]
    except Exception:
        pass

cmd = [adb]
if device_serial:
    cmd.extend(["-s", device_serial])
cmd.extend(["exec-out", "screencap", "-p"])

out_path = Path(out_name)
out_path.parent.mkdir(parents=True, exist_ok=True)

raw = subprocess.check_output(cmd)
with open(out_path, "wb") as f:
    f.write(raw)
print(f"Captured {len(raw)} bytes to {out_path} (device: {device_serial})")
