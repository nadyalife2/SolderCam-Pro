#!/system/bin/sh
# Fix SELinux permissions for battery sysfs under Magisk
magiskpolicy --live "permissive magisk" 2>/dev/null || true
magiskpolicy --live "allow magisk vendor_sysfs_battery_supply file *" 2>/dev/null || true

# Remove carriage returns from all scripts in Termux home
for f in /data/data/com.termux/files/home/*.sh; do
    if [ -f "$f" ]; then
        sed -i 's/\r$//' "$f"
        chmod +x "$f"
    fi
done

# Test writing to battery_charging_enabled
echo 0 > /sys/class/power_supply/battery/battery_charging_enabled 2>/dev/null || true

# Check if battery_guard is running; if not, launch it
if ! pgrep -f battery_guard_24x7.sh >/dev/null; then
    nohup /data/data/com.termux/files/usr/bin/sh /data/data/com.termux/files/home/battery_guard_24x7.sh > /data/data/com.termux/files/home/battery_guard.log 2>&1 &
fi

# Check if thermal_guard is running; if not, launch it
if ! pgrep -f thermal_guard.sh >/dev/null; then
    nohup /data/data/com.termux/files/usr/bin/sh /data/data/com.termux/files/home/thermal_guard.sh > /dev/null 2>&1 &
fi

echo "--- Mi 10T Status Check ---"
echo "battery_charging_enabled: $(cat /sys/class/power_supply/battery/battery_charging_enabled 2>/dev/null)"
echo "capacity: $(cat /sys/class/power_supply/battery/capacity 2>/dev/null)%"
echo "temp: $(cat /sys/class/power_supply/battery/temp 2>/dev/null)"
ps -ef | grep -E "llama|python|guard"
