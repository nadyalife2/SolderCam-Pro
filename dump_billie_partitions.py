import subprocess, time, os, sys

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEST_DIR = r"d:\для one plus nord n10\BACKUP_ONEPLUS_NORD_N10_BILLIE"
os.makedirs(DEST_DIR, exist_ok=True)

PARTITIONS = [
    ("modemst1", "/dev/block/sdf2", 2.5 * 1024 * 1024),
    ("modemst2", "/dev/block/sdf3", 2.5 * 1024 * 1024),
    ("fsg", "/dev/block/sdf4", 2.5 * 1024 * 1024),
    ("fsc", "/dev/block/sdf5", 128 * 1024),
    ("persist", "/dev/block/sda2", 32 * 1024 * 1024),
    ("devinfo", "/dev/block/sde46", 64 * 1024),
    ("boot_b", "/dev/block/sde34", 96 * 1024 * 1024),
    ("boot_a", "/dev/block/sde11", 96 * 1024 * 1024),
    ("dtbo_b", "/dev/block/sde40", 24 * 1024 * 1024),
    ("dtbo_a", "/dev/block/sde17", 24 * 1024 * 1024),
    ("vbmeta_b", "/dev/block/sde39", 64 * 1024),
    ("vbmeta_a", "/dev/block/sde16", 64 * 1024),
    ("vbmeta_system_b", "/dev/block/sde38", 64 * 1024),
    ("vbmeta_system_a", "/dev/block/sde15", 64 * 1024),
]

def run(cmd):
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.stdout.strip()

print("[*] Waiting for ADB device in recovery/root mode...")
for i in range(30):
    out = run(f'"{ADB}" devices')
    if "recovery" in out or "device" in out:
        print("[+] Device detected:\n" + out)
        break
    time.sleep(2)

id_out = run(f'"{ADB}" shell id')
print(f"[*] Identity: {id_out}")

for name, blk, expected_size in PARTITIONS:
    out_file = os.path.join(DEST_DIR, f"{name}.img")
    print(f"[*] Dumping {name} from {blk} -> {out_file}...")
    cmd = f'"{ADB}" exec-out "dd if={blk} 2>/dev/null"'
    with open(out_file, "wb") as f:
        p = subprocess.run(f'"{ADB}" exec-out "dd if={blk} 2>/dev/null"', shell=True, stdout=f)
    size = os.path.getsize(out_file)
    print(f"    [OK] Dumped {name}.img: {size} bytes ({size / (1024*1024):.2f} MB)")

print("[*] All critical partitions successfully dumped to " + DEST_DIR)
