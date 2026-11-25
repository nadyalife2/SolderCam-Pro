#!/data/data/com.termux/files/usr/bin/sh
export HOME="/data/data/com.termux/files/home"
. "$HOME/omni_env.sh"

termux-wake-lock 2>/dev/null
su -c "echo omni_reflex > /sys/power/wake_lock" 2>/dev/null
su -c "iw dev wlan0 set power_save off" 2>/dev/null
pgrep sshd >/dev/null || sshd 2>/dev/null
pkill -f llama-server 2>/dev/null; sleep 1

# VM tuning for zero thrashing (prevent kswapd CPU spikes)
echo 60 > /proc/sys/vm/swappiness 2>/dev/null
echo 50 > /proc/sys/vm/vfs_cache_pressure 2>/dev/null
sync; echo 3 > /proc/sys/vm/drop_caches 2>/dev/null

# :8081 - Reflex Fast LLM (Qwen2.5-3B-Instruct Q4_K_M)
# All cores enabled (threads=2 for compute, rest handle server I/O and OS scheduling)
if [ -f "$HOME/models/qwen2.5-3b-instruct-q4_k_m.gguf" ]; then
  nohup "$LLAMA" -m "$HOME/models/qwen2.5-3b-instruct-q4_k_m.gguf" \
    -c 2048 -b 128 -ub 64 -ctk q8_0 -ctv q8_0 -t 2 -np 1 --host 0.0.0.0 --port 8081 > "$HOME/reflex.log" 2>&1 &
  echo "[OK] Qwen2.5-3B-Instruct reflex daemon launched on :8081"
fi

# :8082 - BGE-M3 (Embeddings, 4 threads)
if [ -f "$HOME/models/bge-m3.gguf" ]; then
  nohup "$LLAMA" -m "$HOME/models/bge-m3.gguf" \
    --embedding --pooling cls -c 1024 -t 4 \
    --host 0.0.0.0 --port 8082 > "$HOME/embed.log" 2>&1 &
  echo "[OK] BGE-M3 embedding daemon launched on :8082"
fi

# Fast-Path Router & Web UI for Melvin App
export PORT=8080
export SECONDARY_PORT=8000
pgrep -f omni_fast_router_v4_9.py >/dev/null || nohup /data/data/com.termux/files/usr/bin/python3 "$HOME/omni_fast_router_v4_9.py" > "$HOME/router.log" 2>&1 &
echo "[OK] Fast-Path Web Router launched on :8080"

# 24/7 Battery Guard
pgrep -f battery_guard_24x7.sh >/dev/null || nohup "$HOME/battery_guard_24x7.sh" > "$HOME/battery_guard.log" 2>&1 &

# Telemetry and Thermal guards
pgrep -f node_telemetry.sh >/dev/null || nohup "$HOME/node_telemetry.sh" nord10 > "$HOME/telemetry.log" 2>&1 &
pgrep -f thermal_guard.sh  >/dev/null || nohup "$HOME/thermal_guard.sh" >/dev/null 2>&1 &

echo "[OK] All Reflex and Router daemons active on Nord N10!"
