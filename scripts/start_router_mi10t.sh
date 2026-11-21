#!/bin/sh
pkill -9 -f "python3.*omni_fast_router" 2>/dev/null
pkill -9 -f "omni_fast_router_v4_9.py" 2>/dev/null
sleep 1
cd /data/data/com.termux/files/home
export HOME=/data/data/com.termux/files/home
export PREFIX=/data/data/com.termux/files/usr
export PATH=/data/data/com.termux/files/usr/bin:$PATH
export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib
/data/local/tmp/run_termux env HOME=$HOME PREFIX=$PREFIX PATH=$PATH LD_LIBRARY_PATH=$LD_LIBRARY_PATH python3 /data/data/com.termux/files/home/omni_fast_router_v4_9.py > /data/data/com.termux/files/home/router.log 2>&1 &
echo "Started"
