#!/system/bin/sh
export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib
trap "" HUP
/data/data/com.termux/files/usr/bin/proot --link2symlink -0 \
  -r /data/data/com.termux/files/home/alpine \
  -b /dev -b /proc -b /sys -b /sdcard:/sdcard -b /data/data/com.termux/files/home:/root \
  -w /root \
  /usr/bin/python3 /root/omni_gateway.py > /data/data/com.termux/files/home/gateway.log 2>&1 &
