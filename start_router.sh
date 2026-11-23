#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Triad-Omni Master Router Launcher (v5.1)
# ==============================================================================
export HOME="/data/data/com.termux/files/home"
export PREFIX="/data/data/com.termux/files/usr"
export PATH="$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$PREFIX/lib"
export PYTHONUNBUFFERED=1
termux-wake-lock 2>/dev/null

DIR="$(cd "$(dirname "$0")" && pwd)"
export NODE_ID="${NODE_ID:-node3}"
export NODE_NAME="${NODE_NAME:-NODE-3 (Master Hub & Telemetry Gateway)}"
export NODE_IP="${NODE_IP:-192.168.31.48}"
export PORT="${PORT:-8000}"
export SECONDARY_PORT="${SECONDARY_PORT:-5000}"

pkill -f omni_fast_router_v4_9.py 2>/dev/null
sleep 0.5

ROUTER_SCRIPT="$DIR/scripts/omni_fast_router_v4_9.py"
if [ ! -f "$ROUTER_SCRIPT" ]; then
    ROUTER_SCRIPT="$HOME/scripts/omni_fast_router_v4_9.py"
fi
if [ ! -f "$ROUTER_SCRIPT" ]; then
    ROUTER_SCRIPT="$DIR/omni_fast_router_v4_9.py"
fi
if [ ! -f "$ROUTER_SCRIPT" ]; then
    ROUTER_SCRIPT="$HOME/omni_fast_router_v4_9.py"
fi

if [ ! -f "$ROUTER_SCRIPT" ]; then
    echo "❌ [ERROR] omni_fast_router_v4_9.py not found!"
    exit 1
fi

nohup python3 "$ROUTER_SCRIPT" > "$HOME/router.log" 2>&1 &
sleep 1.5

if pgrep -f omni_fast_router_v4_9.py >/dev/null; then
    echo "✅ [OK] Master Router successfully running on port $PORT (secondary: $SECONDARY_PORT)!"
else
    echo "❌ [ERROR] Router failed to start. Last log lines:"
    tail -n 15 "$HOME/router.log" 2>/dev/null
    exit 1
fi
