#!/data/data/com.termux/files/usr/bin/bash
export HOME="/data/data/com.termux/files/home"
export PREFIX="/data/data/com.termux/files/usr"
export PATH="$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$PREFIX/lib"
cd "$HOME"
pkill -9 -f omni_fast_router_v4_9.py 2>/dev/null
sleep 1
exec /data/data/com.termux/files/usr/bin/python3 omni_fast_router_v4_9.py
