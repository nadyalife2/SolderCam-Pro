#!/data/data/com.termux/files/usr/bin/bash
export HOME="/data/data/com.termux/files/home"
export PREFIX="/data/data/com.termux/files/usr"
export PATH="$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="/data/data/com.termux/files/home/llama.cpp/build/bin:$PREFIX/lib"
export OMP_NUM_THREADS=4
export GGML_OPENMP=1

echo omni_brain > /sys/power/wake_lock 2>/dev/null
iw dev wlan0 set power_save off 2>/dev/null

# Port forwarding: перенаправление локального порта 8000 на 8080 для мгновенного входа в веб-интерфейс из приложения
iptables -t nat -C OUTPUT -p tcp -d 127.0.0.1 --dport 8000 -j REDIRECT --to-port 8080 2>/dev/null || \
iptables -t nat -A OUTPUT -p tcp -d 127.0.0.1 --dport 8000 -j REDIRECT --to-port 8080 2>/dev/null

# Daemons
pgrep sshd >/dev/null || $PREFIX/bin/sshd
pgrep -f battery_guard_24x7.sh >/dev/null || nohup "$HOME/battery_guard_24x7.sh" >/dev/null 2>&1 &
pgrep -f thermal_guard.sh >/dev/null || nohup "$HOME/thermal_guard.sh" >/dev/null 2>&1 &
pgrep -f node_telemetry.sh >/dev/null || nohup "$HOME/node_telemetry.sh" >/dev/null 2>&1 &

MODEL_FILE="$HOME/models/brain.gguf"
LLAMA="$HOME/llama.cpp/build/bin/llama-server"

pkill -f llama-server 2>/dev/null
sleep 1

# Master Blueprint Launch v5.0:
# -np 1: 100% KV-кэша отдано монопольному слоту ассистента (без накладных расходов 4 слотов)
# --swa-full: полный размер SWA-кэша для включения KV-shifting на Qwen 3.5
# -ctk f16 -ctv f16: полноточный KV-кэш для стабильного кэширования
# -b 256 -ub 64: калибровка под L2/L3 кэш ядер Kryo 585 (Gold/Prime)
# -lcd "$HOME/lookup.cache": Dynamic Prompt Lookup Decoding
# --cache-reuse 256: мгновенный prefill системного промпта (<50 мс вместо 34 с)
nohup taskset -c 4,5,6,7 "$LLAMA" \
  -m "$MODEL_FILE" \
  --host 0.0.0.0 --port 8080 \
  --path "$HOME/web_ui" \
  -np 1 \
  -t 4 -tb 4 \
  -c 4096 \
  -b 256 -ub 64 \
  -ctk f16 -ctv f16 \
  --swa-full \
  -lcd "$HOME/lookup.cache" \
  --cache-reuse 256 > "$HOME/brain.log" 2>&1 &

echo "Triad-Omni Brain v5.0 (Single-Slot Hot-Cache) launched on port 8080!"
