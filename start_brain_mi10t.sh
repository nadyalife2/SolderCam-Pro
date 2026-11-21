#!/data/data/com.termux/files/usr/bin/bash
export HOME="/data/data/com.termux/files/home"
export PREFIX="/data/data/com.termux/files/usr"
export PATH="$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="/data/data/com.termux/files/home/llama.cpp/build/bin:$PREFIX/lib"

echo omni_brain > /sys/power/wake_lock 2>/dev/null
iw dev wlan0 set power_save off 2>/dev/null

# Daemons
pgrep sshd >/dev/null || $PREFIX/bin/sshd
pgrep -f battery_guard_24x7.sh >/dev/null || nohup "$HOME/battery_guard_24x7.sh" >/dev/null 2>&1 &
pgrep -f thermal_guard.sh >/dev/null || nohup "$HOME/thermal_guard.sh" >/dev/null 2>&1 &
pgrep -f node_telemetry.sh >/dev/null || nohup "$HOME/node_telemetry.sh" >/dev/null 2>&1 &

MODEL_FILE="$HOME/models/brain.gguf"
LLAMA="$HOME/llama.cpp/build/bin/llama-server"

pkill -f llama-server 2>/dev/null
sleep 1

nohup taskset -c 4,5,6,7 "$LLAMA" -m "$MODEL_FILE" \
  -c 4096 -b 512 -ub 512 --cache-reuse 256 \
  -t 4 -np 1 --host 0.0.0.0 --port 8080 > "$HOME/brain.log" 2>&1 &

echo "OPTIMIZED Main Brain launched on port 8080 with KV cache-reuse 256!"
