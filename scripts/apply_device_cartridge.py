import subprocess
import json
from pathlib import Path

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
CARD_PATH = Path(r"d:\для one plus nord n10\models\card.json")

slug = "triad-omni-cartridge"
build_tag = "cartridge"
if CARD_PATH.exists():
    try:
        with open(CARD_PATH, "r", encoding="utf-8") as f:
            c = json.load(f)
            slug = c.get("slug", slug)
            build_tag = c.get("build_tag", c.get("version", build_tag))
    except Exception:
        pass

sh_script = f"""
H=/data/data/com.termux/files/home
mkdir -p "$H/cartridges/{build_tag}" "$H/models" "$H/config"
cp -f /data/local/tmp/adapter.gguf "$H/cartridges/{build_tag}/adapter.gguf"
cp -f /data/local/tmp/card.json "$H/cartridges/{build_tag}/card.json"
cp -f /data/local/tmp/adapter.gguf "$H/models/adapter.gguf"
cp -f /data/local/tmp/card.json "$H/models/card.json"
echo '{{"active": true, "build_tag": "{build_tag}", "slug": "{slug}", "scale": 1.0}}' > "$H/config/active_cartridge.json"
chown -R u0_a212:u0_a212 "$H/cartridges" "$H/models" "$H/config"
chmod -R 755 "$H/cartridges" "$H/models" "$H/config"
ls -lh "$H/models/adapter.gguf" "$H/models/card.json" "$H/cartridges/{build_tag}/adapter.gguf"
rm -f /data/local/tmp/adapter.gguf /data/local/tmp/card.json
"""

p = subprocess.run([ADB, "shell", f"su -c '{sh_script}'"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
print("STDOUT:\n", p.stdout)
print("STDERR:\n", p.stderr)
