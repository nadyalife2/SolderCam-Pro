#!/system/bin/sh
# Triad-Omni Node-2 (OnePlus Nord N10 5G) Magisk Boot Service
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 2
done
sleep 5

# Wireless ADB 24/7 on port 5555
setprop service.adb.tcp.port 5555
stop adbd
start adbd

# Execute Watchdog & Bridge
sh /data/local/tmp/start_melvin.sh > /sdcard/melvin_boot.log 2>&1
