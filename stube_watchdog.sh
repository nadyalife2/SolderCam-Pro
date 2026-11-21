#!/system/bin/sh
# ==============================================================================
# SolderCam Pro & Edge Projector - SmartTube Auto-Proxy Watchdog Daemon v2.0
# Real-time event-driven trigger (<20ms) + 3s self-healing active health-check
# Automatically starts optimized ciadpi proxy when SmartTube enters foreground
# Automatically stops ciadpi when SmartTube is closed/backgrounded (saves RAM/CPU)
# Recovers ciadpi automatically if terminated by OOM / signal during playback
# ==============================================================================

trap '' HUP INT TERM

CIADPI_BIN="/system/bin/ciadpi"
PID_FILE="/data/local/tmp/ciadpi.pid"
STUBE_PKG="org.smarttube.beta"

apply_tcp_tuning() {
    echo "524288 1048576 4194304" > /proc/sys/net/ipv4/tcp_rmem 2>/dev/null
    echo "262144 524288 2097152" > /proc/sys/net/ipv4/tcp_wmem 2>/dev/null
    echo 4194304 > /proc/sys/net/core/rmem_max 2>/dev/null
    echo 2097152 > /proc/sys/net/core/wmem_max 2>/dev/null
    echo 3 > /proc/sys/net/ipv4/tcp_fastopen 2>/dev/null
    echo 30 > /proc/sys/net/ipv4/tcp_keepalive_time 2>/dev/null
    echo 5 > /proc/sys/net/ipv4/tcp_keepalive_intvl 2>/dev/null
    echo 3 > /proc/sys/net/ipv4/tcp_keepalive_probes 2>/dev/null
}

is_ciadpi_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            return 0
        fi
    fi
    pidof ciadpi >/dev/null 2>&1
}

start_ciadpi() {
    if ! is_ciadpi_running; then
        pkill -9 -f "$CIADPI_BIN" 2>/dev/null
        rm -f "$PID_FILE"

        apply_tcp_tuning
        $CIADPI_BIN -i 127.0.0.1 -p 1080 -D -b 65536 -c 256 -d 1 -s 3+s -s 6+s -s 12+s -s 20+s -s 30+s -K tls,http -w "$PID_FILE"
        log -t STUBE_WATCHDOG "ciadpi started for SmartTube Beta (PID=$(pidof ciadpi))"
    fi
}

stop_ciadpi() {
    if is_ciadpi_running; then
        CPID=$(pidof ciadpi 2>/dev/null)
        if [ -n "$CPID" ]; then
            kill -15 $CPID 2>/dev/null
            sleep 0.1
            kill -9 $CPID 2>/dev/null
        fi
        pkill -9 -f "$CIADPI_BIN" 2>/dev/null
        rm -f "$PID_FILE"
        log -t STUBE_WATCHDOG "ciadpi stopped (SmartTube backgrounded/exited)"
    fi
}

is_stube_focused() {
    dumpsys window 2>/dev/null | grep -q "mCurrentFocus.*$STUBE_PKG"
}

check_health() {
    if is_stube_focused; then
        if ! is_ciadpi_running; then
            log -t STUBE_WATCHDOG "ciadpi self-heal: process died while SmartTube in foreground, restarting..."
            start_ciadpi
        fi
    else
        if is_ciadpi_running; then
            log -t STUBE_WATCHDOG "ciadpi cleanup: running while SmartTube not focused, stopping..."
            stop_ciadpi
        fi
    fi
}

# Initial synchronization
check_health

# Hybrid Engine: Real-time event pipe with 3-second health-check fallback
while true; do
    logcat -v tag -T 1 -b events -s am_focused_activity:I | while true; do
        if read -t 3 -r line; then
            case "$line" in
                *$STUBE_PKG*)
                    start_ciadpi
                    ;;
                *NULL*)
                    ;;
                *)
                    stop_ciadpi
                    ;;
            esac
        else
            check_health
        fi
    done
    sleep 2
done
