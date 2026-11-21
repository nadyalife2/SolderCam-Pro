#!/data/data/com.termux/files/usr/bin/bash
export PREFIX="/data/data/com.termux/files/usr"
export PATH="$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$PREFIX/lib"
export PYTHONUNBUFFERED=1
termux-wake-lock 2>/dev/null
cd /data/data/com.termux/files/home
export NODE_ID="node3"
export NODE_NAME="NODE-3 (Master Hub & Telemetry Gateway)"
export NODE_IP="192.168.31.48"
export PORT=8000
export SECONDARY_PORT=8080
pkill -f omni_fast_router_v4_9.py 2>/dev/null
sleep 0.5
nohup python omni_fast_router_v4_9.py > router.log 2>&1 &
sleep 1
echo "[OK] Router running on ports 8000 & 8080"
