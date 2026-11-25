#!/system/bin/sh
# ==============================================================================
# Triad-Omni Node-2 (OnePlus Nord N10 5G) Autonomous Watchdog & Bridge
# ==============================================================================
echo "=== [WATCHDOG] Triad-Omni Node-2 Launching... ==="

# 1. Hardware WakeLock and Wi-Fi performance lock
echo omni_melvin > /sys/power/wake_lock 2>/dev/null
iw dev wlan0 set power_save off 2>/dev/null

# 2. Maintain Wireless ADB active 24/7 on port 5555
setprop service.adb.tcp.port 5555
if ! getprop init.svc.adbd | grep -q "running"; then
    start adbd 2>/dev/null
fi

# 3. Check if Reflex (:8081) and Router (:8080) are already alive
if ! /system/bin/toybox netstat -tlpn 2>/dev/null | grep -qE ":8081|:8080"; then
    echo "⚡ Services offline. Waking up Termux Activity..."
    
    # Wake up screen if sleeping and launch Termux in background
    input keyevent 224 2>/dev/null
    am start -n com.termux/.app.TermuxActivity 2>/dev/null
    sleep 1.5
    
    # Launch Qwen2.5-3B + BGE-M3 + Router via start_reflex.sh
    export HOME="/data/data/com.termux/files/home"
    su -g 10234 -G 3003 u0_a234 -c "sh /data/data/com.termux/files/home/start_reflex.sh" || \
    su -c "sh /data/data/com.termux/files/home/start_reflex.sh"
    
    sleep 2
    echo "✅ [WATCHDOG] Node-2 Services successfully resurrected!"
else
    echo "✅ [WATCHDOG] Node-2 Services already active."
fi

# 4. Bring Triad-Omni App back to foreground
am start -n ai.melvin.app/.MainActivity 2>/dev/null
