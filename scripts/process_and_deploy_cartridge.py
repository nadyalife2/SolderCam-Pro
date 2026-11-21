import os
import sys
import time
import zipfile
import json
import hashlib
from pathlib import Path

BASE_DIR = Path(r"d:\для one plus nord n10")
ZIP_PATH = BASE_DIR / "cartridges" / "cartridge_new.zip"
TARGET_DIR = BASE_DIR / "cartridges" / "v3_tochka_rea"
MODELS_DIR = BASE_DIR / "models"
EXPECTED_SIZE = 149407322

print(f"Waiting for download to finish ({EXPECTED_SIZE} bytes)...")
max_wait = 180
waited = 0
while waited < max_wait:
    if ZIP_PATH.exists():
        current_size = ZIP_PATH.stat().st_size
        if current_size >= EXPECTED_SIZE:
            print(f"File fully downloaded: {current_size} bytes ({current_size / (1024*1024):.2f} MB)")
            break
        print(f"Progress: {current_size / (1024*1024):.2f} MB / {EXPECTED_SIZE / (1024*1024):.2f} MB...", end="\r")
    time.sleep(2)
    waited += 2

print("\nExtracting archive...")
TARGET_DIR.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(ZIP_PATH, "r") as zf:
    zf.extractall(TARGET_DIR)
    file_list = zf.namelist()
    print("Files in archive:")
    for f in file_list:
        p = TARGET_DIR / f
        sz = p.stat().st_size if p.is_file() else 0
        print(f"  - {f}: {sz / (1024*1024):.2f} MB")

# Check card.json
card_path = TARGET_DIR / "card.json"
card_data = {}
if card_path.exists():
    with open(card_path, "r", encoding="utf-8") as f:
        card_data = json.load(f)
    print("\nCard.json loaded:")
    print(json.dumps(card_data, indent=2, ensure_ascii=False))
else:
    print("\nWarning: card.json not found in archive, generating default card.json...")
    card_data = {
        "name": "Triad-Omni Tochka Plavleniya + REA LoRA",
        "slug": "tochka_rea_v3",
        "version": "v3.0",
        "build_tag": "colab_tesla_t4_352s",
        "samples": 352,
        "lora_r": 16,
        "lora_alpha": 16,
        "target_model": "Qwen2.5-Coder-7B-Instruct / Qwen3.5-9B",
        "author": "Antigravity + Practico Editorial & Reverse Engineering",
        "description": "LoRA-адаптер с полными знаниями ГОСТ Р 56427-2022, IPC-A-610J, IPC J-STD-001J, IPC-7095E, IPC-7093A и REA"
    }
    with open(card_path, "w", encoding="utf-8") as f:
        json.dump(card_data, f, indent=2, ensure_ascii=False)

# Check adapter.gguf
gguf_files = list(TARGET_DIR.glob("*.gguf"))
if not gguf_files:
    gguf_files = list(TARGET_DIR.rglob("*.gguf"))

if gguf_files:
    gguf_file = gguf_files[0]
    print(f"\nFound GGUF adapter: {gguf_file.name} ({gguf_file.stat().st_size / (1024*1024):.2f} MB)")
    with open(gguf_file, "rb") as f:
        magic = f.read(4)
        print(f"GGUF Magic: {magic} ({'VALID GGUF' if magic == b'GGUF' else 'INVALID'})")
    
    # Copy to models/
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    dest_adapter = MODELS_DIR / "adapter.gguf"
    import shutil
    shutil.copy2(gguf_file, dest_adapter)
    shutil.copy2(card_path, MODELS_DIR / "card.json")
    print(f"Copied to {dest_adapter} and {MODELS_DIR / 'card.json'}")
else:
    print("\nError: No .gguf files found in unpacked archive!")
