#!/data/data/com.termux/files/usr/bin/bash
export HOME="/data/data/com.termux/files/home"
export PREFIX="/data/data/com.termux/files/usr"
export PATH="$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="/data/data/com.termux/files/home/llama.cpp/build/bin:$PREFIX/lib"
export OMP_NUM_THREADS=4
export GGML_OPENMP=1

echo omni_brain > /sys/power/wake_lock 2>/dev/null
iw dev wlan0 set power_save off 2>/dev/null

# Daemons
pgrep sshd >/dev/null || $PREFIX/bin/sshd
pgrep -f battery_guard_24x7.sh >/dev/null || nohup "$HOME/battery_guard_24x7.sh" >/dev/null 2>&1 &
pgrep -f thermal_guard.sh >/dev/null || nohup "$HOME/thermal_guard.sh" >/dev/null 2>&1 &
pgrep -f node_telemetry.sh >/dev/null || nohup "$HOME/node_telemetry.sh" >/dev/null 2>&1 &

MODEL_FILE="$HOME/models/brain.gguf"
ADAPTER_FILE="$HOME/models/adapter.gguf"
LLAMA="$HOME/llama.cpp/build/bin/llama-server"

killall -9 llama-server 2>/dev/null
sleep 1

LORA_FLAG=""
if [ -f "$ADAPTER_FILE" ]; then
    LORA_FLAG="--lora $ADAPTER_FILE"
fi

# Master Blueprint Launch v5.2:
nohup taskset -c 4,5,6,7 "$LLAMA" \
  -m "$MODEL_FILE" \
  $LORA_FLAG \
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

echo "Triad-Omni Brain v5.2 launched with active LoRA on port 8080!"
