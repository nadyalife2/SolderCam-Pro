#!/system/bin/sh
H="/data/data/com.termux/files/home"
mkdir -p "$H/cartridges/v3_tochka_rea" "$H/models" "$H/config"
cp -f /data/local/tmp/adapter.gguf "$H/cartridges/v3_tochka_rea/adapter.gguf"
cp -f /data/local/tmp/card.json "$H/cartridges/v3_tochka_rea/card.json"
cp -f /data/local/tmp/adapter.gguf "$H/models/adapter.gguf"
cp -f /data/local/tmp/card.json "$H/models/card.json"
echo '{"active": true, "build_tag": "v3_tochka_rea", "slug": "triad-omni-persona", "scale": 1.0}' > "$H/config/active_cartridge.json"
chown -R u0_a212:u0_a212 "$H/cartridges" "$H/models" "$H/config"
chmod -R 755 "$H/cartridges" "$H/models" "$H/config"
ls -lh "$H/models/adapter.gguf" "$H/models/card.json" "$H/cartridges/v3_tochka_rea/adapter.gguf"
rm -f /data/local/tmp/adapter.gguf /data/local/tmp/card.json
