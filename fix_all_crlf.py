import os
import subprocess
from nord_tool import su, get_nord_device

print("1. Fixing line endings across host workspace...")
count = 0
for root, dirs, files in os.walk('.'):
    for f in files:
        if any(f.endswith(ext) for ext in ['.sh', '.py', '.env']):
            p = os.path.join(root, f)
            with open(p, 'rb') as fp:
                data = fp.read()
            if b'\r\n' in data:
                data = data.replace(b'\r\n', b'\n')
                with open(p, 'wb') as fp:
                    fp.write(data)
                count += 1
print(f"Fixed {count} files on host.")

print("2. Pushing fixed scripts to Node-2...")
ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
dev = get_nord_device()

for s in ["scripts/battery_guard_24x7.sh", "start_reflex.sh", "download_models.sh", "scripts/omni_fast_router_v4_9.py"]:
    fname = os.path.basename(s)
    subprocess.run([ADB, "-s", dev, "push", s, f"/data/local/tmp/{fname}"], check=True, capture_output=True)
    su(f"cp /data/local/tmp/{fname} /data/data/com.termux/files/home/{fname}")
    su(f"chmod 755 /data/data/com.termux/files/home/{fname}")
    su(f"chown u0_a234:u0_a234 /data/data/com.termux/files/home/{fname}")

# Also copy start_reflex.sh to .termux/boot
su("cp /data/data/com.termux/files/home/start_reflex.sh /data/data/com.termux/files/home/.termux/boot/start_reflex.sh")
su("chmod 755 /data/data/com.termux/files/home/.termux/boot/start_reflex.sh")

# Strip \r on device
su("dos2unix /data/data/com.termux/files/home/*.sh 2>/dev/null || sed -i -e 's/\\r$//' /data/data/com.termux/files/home/*.sh")

print("3. Testing battery_guard_24x7 execution...")
su("pkill -f battery_guard_24x7.sh || true")
su("nohup /data/data/com.termux/files/home/battery_guard_24x7.sh </dev/null >/data/data/com.termux/files/home/battery_guard.log 2>&1 &")
import time
time.sleep(3)
out, _ = su("cat /data/data/com.termux/files/home/battery_guard.log")
print("Battery Guard Output:")
print(out)
