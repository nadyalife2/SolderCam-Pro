#!/system/bin/sh
# Triad-Omni Node-1 (Xiaomi Mi 10T 5G) Boot Autostart Service
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 2
done
sleep 5

# Keep wireless ADB active 24/7 for remote wake-up
setprop service.adb.tcp.port 5555
stop adbd
start adbd

echo omni_boot > /sys/power/wake_lock 2>/dev/null
iw dev wlan0 set power_save off 2>/dev/null

# Hardware battery bypass for 24/7 cluster longevity
echo 0 > /sys/class/power_supply/battery/battery_charging_enabled 2>/dev/null || true

# Start Termux Activity and Brain services
am start -n com.termux/.app.TermuxActivity
sleep 3

su -g 10212 -G 3003 u0_a212 -c "/data/data/com.termux/files/usr/bin/sh /data/data/com.termux/files/home/start_brain.sh" || \
su -c "sh /data/data/com.termux/files/home/start_brain.sh"

sleep 2
# Start Router on Node-1
su -c "export HOME=/data/data/com.termux/files/home; export NODE_ID=node1; export PORT=8000; nohup /data/data/com.termux/files/usr/bin/python3 /data/data/com.termux/files/home/omni_fast_router_v4_9.py > /data/data/com.termux/files/home/router.log 2>&1 &"
