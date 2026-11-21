#!/system/bin/sh
sleep 5

# --- 1. TorrServer Port Redirection (3191 -> 8090) ---
iptables -t nat -D PREROUTING -p tcp --dport 3191 -j REDIRECT --to-ports 8090 2>/dev/null
iptables -t nat -A PREROUTING -p tcp --dport 3191 -j REDIRECT --to-ports 8090
iptables -t nat -D OUTPUT -p tcp -o lo --dport 3191 -j REDIRECT --to-ports 8090 2>/dev/null
iptables -t nat -A OUTPUT -p tcp -o lo --dport 3191 -j REDIRECT --to-ports 8090

# --- 2. Launch TorrServer Native Daemon ---
if ! pgrep -f TorrServer > /dev/null; then
    mkdir -p /data/data/ru.yourok.torrserve/files/db
    /data/data/ru.yourok.torrserve/files/TorrServer -d /data/data/ru.yourok.torrserve/files/db -p 8090 > /data/data/ru.yourok.torrserve/files/torr.log 2>&1 &
fi

# --- 3. Clean DNS Settings ---
setprop net.dns1 77.88.8.8
setprop net.dns2 8.8.8.8

# --- 4. SmartTube Beta Dynamic Auto-Proxy Watchdog Daemon ---
pkill -f stube_watchdog.sh 2>/dev/null
setsid /system/bin/stube_watchdog.sh </dev/null >/dev/null 2>&1 &

