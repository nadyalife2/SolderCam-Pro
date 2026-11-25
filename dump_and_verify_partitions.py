import os
import sys
import time
import json
import hashlib
import subprocess

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "50fb497c"
BACKUP_DIR = r"d:\для one plus nord n10\backups\partitions_nord_n10"

PARTITIONS = [
    # EFS / NVRAM / IMEI
    "modemst1",
    "modemst2",
    "fsg",
    "fsc",
    # Calibration / Sensors
    "persist",
    # Boot & Kernel
    "boot_a",
    "boot_b",
    "dtbo_a",
    "dtbo_b",
    "vbmeta_a",
    "vbmeta_b",
    # Extra critical safeguards
    "vbmeta_system_a",
    "vbmeta_system_b",
    "recovery_a",
    "recovery_b",
    "param",
    "devinfo"
]

def run_cmd(args):
    return subprocess.run(args, capture_output=True, text=True)

def get_device_sha256_and_size(part):
    dev_path = f"/dev/block/by-name/{part}"
    cmd_sz = [ADB, "-s", DEVICE, "shell", "su", "-c", f"blockdev --getsize64 {dev_path}"]
    res_sz = run_cmd(cmd_sz)
    if res_sz.returncode != 0:
        raise RuntimeError(f"Failed to get size for {part}: {res_sz.stderr}")
    expected_size = int(res_sz.stdout.strip())

    cmd_hash = [ADB, "-s", DEVICE, "shell", "su", "-c", f"sha256sum {dev_path}"]
    res_hash = run_cmd(cmd_hash)
    if res_hash.returncode != 0:
        raise RuntimeError(f"Failed to get sha256 for {part}: {res_hash.stderr}")
    device_sha256 = res_hash.stdout.strip().split()[0]
    return expected_size, device_sha256

def dump_partition(part, out_file):
    dev_path = f"/dev/block/by-name/{part}"
    cmd = [ADB, "-s", DEVICE, "exec-out", "su", "-c", f"dd if={dev_path} bs=1M status=none"]
    with open(out_file, "wb") as f:
        res = subprocess.run(cmd, stdout=f)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to dd partition {part}")

def get_file_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print("=" * 60)
    print("ONEPLUS NORD N10 5G (BE2029) CRITICAL PARTITION DUMPER & VERIFIER")
    print(f"Device: {DEVICE}")
    print(f"Output Directory: {BACKUP_DIR}")
    print("=" * 60)

    # Clean old test files if any
    test_fsc = os.path.join(BACKUP_DIR, "test_fsc.img")
    if os.path.exists(test_fsc):
        os.remove(test_fsc)

    manifest = {
        "device": "OnePlus Nord N10 5G (billie / BE2029)",
        "serial": DEVICE,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "partitions": {}
    }

    checksum_lines = []

    for idx, part in enumerate(PARTITIONS, 1):
        out_img = os.path.join(BACKUP_DIR, f"{part}.img")
        print(f"[{idx}/{len(PARTITIONS)}] Processing {part}...")
        
        t0 = time.time()
        expected_size, device_hash = get_device_sha256_and_size(part)
        print(f"   Device: {expected_size} bytes, SHA256: {device_hash}")

        dump_partition(part, out_img)
        actual_size = os.path.getsize(out_img)
        local_hash = get_file_sha256(out_img)
        dt = time.time() - t0

        if actual_size != expected_size:
            print(f"   [ERROR] Size mismatch: expected {expected_size}, got {actual_size}")
            sys.exit(1)

        if local_hash != device_hash:
            print(f"   [ERROR] Hash mismatch:\n   Device: {device_hash}\n   Local:  {local_hash}")
            sys.exit(1)

        print(f"   [OK] Verified! ({actual_size / (1024*1024):.2f} MB in {dt:.1f}s) Checksum: {local_hash[:16]}...")
        
        manifest["partitions"][part] = {
            "size_bytes": actual_size,
            "sha256": local_hash,
            "verified": True
        }
        checksum_lines.append(f"{local_hash}  {part}.img")

    # Save manifest and checksums
    manifest_path = os.path.join(BACKUP_DIR, "partition_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    checksum_path = os.path.join(BACKUP_DIR, "checksums_nord_n10.txt")
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write("\n".join(checksum_lines) + "\n")

    print("=" * 60)
    print("ALL 17 CRITICAL PARTITIONS DUMPED AND VERIFIED BIT-FOR-BIT!")
    print(f"Manifest written to: {manifest_path}")
    print(f"Checksums written to: {checksum_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
