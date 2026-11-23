#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
# Triad-Omni Brain Launcher v5.3 (Mi 10T / Apollo / Snapdragon 865)
# Запускает: sshd, battery_guard, thermal_guard, node_telemetry, router, llama-server
# Исправлены: контекст 16384, KV q8_0, batch 512, LoRA-адаптер, проверка запуска
# =============================================================================

export HOME="/data/data/com.termux/files/home"
export PREFIX="/data/data/com.termux/files/usr"
export PATH="$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/llama.cpp/build/bin:$PREFIX/lib"
export OMP_NUM_THREADS=4
export GGML_OPENMP=1

echo omni_brain > /sys/power/wake_lock 2>/dev/null
iw dev wlan0 set power_save off 2>/dev/null

# --- Daemons ---
pgrep sshd >/dev/null || $PREFIX/bin/sshd
pgrep -f battery_guard_24x7.sh >/dev/null || nohup "$HOME/battery_guard_24x7.sh" >/dev/null 2>&1 &
pgrep -f thermal_guard.sh >/dev/null || nohup "$HOME/thermal_guard.sh" >/dev/null 2>&1 &
pgrep -f node_telemetry.sh >/dev/null || nohup "$HOME/node_telemetry.sh" >/dev/null 2>&1 &

# --- Master Web Router v5.0 on port 8000 ---
pgrep -f omni_fast_router_v4_9.py >/dev/null || nohup python3 "$HOME/omni_fast_router_v4_9.py" > "$HOME/router.log" 2>&1 &

# --- Brain LLM (llama-server) on port 8080 ---
MODEL_FILE="$HOME/models/brain.gguf"
ADAPTER_FILE="$HOME/models/adapter.gguf"
LLAMA="$HOME/llama.cpp/build/bin/llama-server"

if [ ! -f "$MODEL_FILE" ]; then
    echo "ERROR: Model file $MODEL_FILE not found!"
    exit 1
fi

if [ ! -f "$LLAMA" ]; then
    echo "ERROR: llama-server binary not found at $LLAMA"
    exit 1
fi

killall -9 llama-server 2>/dev/null
sleep 1

# Native Clean Mode: Running without --lora restores 100% ARM CPU_REPACK vector speed (+35% t/s)
# LORA_FLAG=""
# if [ -f "$ADAPTER_FILE" ]; then
#     LORA_FLAG="--lora $ADAPTER_FILE"
# fi

# Optimization: -ub 256 for Cortex-A77 L2/L3 cache, removed unsupported --swa-full and --cache-reuse
nohup taskset -c 4,5,6,7 "$LLAMA" \
  -m "$MODEL_FILE" \
  --host 0.0.0.0 --port 8080 \
  --path "$HOME/web_ui" \
  -np 1 \
  -t 4 -tb 4 \
  -c 16384 \
  -b 512 -ub 256 \
  -ctk q8_0 -ctv q8_0 \
  -lcd "$HOME/lookup.cache" > "$HOME/brain.log" 2>&1 &

BRAIN_PID=$!
sleep 2

if kill -0 "$BRAIN_PID" 2>/dev/null; then
    echo "Triad-Omni Brain v5.3 launched (PID $BRAIN_PID) on port 8080 + Router on 8000"
else
    echo "ERROR: Brain process died immediately! Check brain.log:"
    tail -20 "$HOME/brain.log"
    exit 1
fi
