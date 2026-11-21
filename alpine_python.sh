#!/data/data/com.termux/files/usr/bin/sh
unset LD_PRELOAD
export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib
export PATH=/data/data/com.termux/files/usr/bin:$PATH
exec /data/data/com.termux/files/usr/bin/proot --link2symlink -0 -r /data/data/com.termux/files/home/alpine \
  -b /dev -b /proc -b /sys -b /sdcard:/sdcard -b /data/data/com.termux/files/home:/root \
  -w /root \
  /usr/bin/env -i \
  HOME=/root \
  TERM=xterm-256color \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  python3 "$@"
