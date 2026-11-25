import os
import sys
import time
import urllib.request

MODEL_URL = "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
DEST_DIR = r"d:\для one plus nord n10\models"
DEST_FILE = os.path.join(DEST_DIR, "qwen2.5-3b-instruct-q4_k_m.gguf")
PART_FILE = DEST_FILE + ".part"
EXPECTED_SIZE = 2104932768

def download_loop():
    os.makedirs(DEST_DIR, exist_ok=True)
    if os.path.exists(DEST_FILE):
        size = os.path.getsize(DEST_FILE)
        print(f"Model already exists at {DEST_FILE} (size: {size} bytes)")
        if size == EXPECTED_SIZE:
            print("File is complete and valid!")
            return True

    while True:
        existing_bytes = os.path.getsize(PART_FILE) if os.path.exists(PART_FILE) else 0
        if existing_bytes >= EXPECTED_SIZE:
            if os.path.exists(DEST_FILE):
                os.remove(DEST_FILE)
            os.rename(PART_FILE, DEST_FILE)
            print(f"Download complete! Final size: {os.path.getsize(DEST_FILE)}")
            return True

        pct = (existing_bytes / EXPECTED_SIZE) * 100
        print(f"Resuming download from byte {existing_bytes} / {EXPECTED_SIZE} ({pct:.1f}%)...")

        req = urllib.request.Request(
            MODEL_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Range": f"bytes={existing_bytes}-"
            }
        )

        t0 = time.time()
        last_print = t0
        downloaded_session = 0

        try:
            with urllib.request.urlopen(req, timeout=30) as resp, open(PART_FILE, "ab") as f:
                chunk_size = 1024 * 512
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded_session += len(chunk)
                    cur_total = existing_bytes + downloaded_session

                    now = time.time()
                    if now - last_print >= 5:
                        speed = downloaded_session / (now - t0) / (1024 * 1024)
                        pct = (cur_total / EXPECTED_SIZE) * 100
                        print(f"Downloaded: {cur_total / (1024*1024):.1f}/{EXPECTED_SIZE / (1024*1024):.1f} MB ({pct:.1f}%) @ {speed:.2f} MB/s")
                        last_print = now

            if os.path.getsize(PART_FILE) >= EXPECTED_SIZE:
                if os.path.exists(DEST_FILE):
                    os.remove(DEST_FILE)
                os.rename(PART_FILE, DEST_FILE)
                print(f"Download fully complete: {DEST_FILE} ({os.path.getsize(DEST_FILE)} bytes)")
                return True
            else:
                print(f"Connection ended early ({os.path.getsize(PART_FILE)} < {EXPECTED_SIZE}), retrying in 2 seconds...")
                time.sleep(2)
        except Exception as e:
            print(f"Transient error: {e}. Retrying in 3 seconds...")
            time.sleep(3)

def main():
    download_loop()

if __name__ == "__main__":
    main()

