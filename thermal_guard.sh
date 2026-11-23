#!/data/data/com.termux/files/usr/bin/sh
HOT=48000; COOL=43000; STATE=norm
maxtemp() {
    M=0
    for z in /sys/class/thermal/thermal_zone*; do
        case "$(cat "$z/type" 2>/dev/null)" in
          *cpu*|*soc*|*tsens*|*apc*|*gpuss*) V=$(cat "$z/temp" 2>/dev/null || echo 0)
             [ "$V" -gt "$M" ] 2>/dev/null && M=$V ;;
        esac
    done
    echo "$M"
}
setcap() {
    target_freq="$1"
    # Auto-detect big and prime core policies across Snapdragon 865 (policy4, policy7) and SD690 (policy6)
    for p in /sys/devices/system/cpu/cpufreq/policy[4-7]; do
        if [ -d "$p" ]; then
            BEST=""
            for f in $(cat "$p/scaling_available_frequencies" 2>/dev/null); do
                [ "$f" -le "$target_freq" ] && BEST=$f
            done
            if [ -n "$BEST" ]; then
                echo "$BEST" > "$p/scaling_max_freq" 2>/dev/null || su -c "echo $BEST > $p/scaling_max_freq" 2>/dev/null
            fi
        fi
    done
}
while true; do
    T=$(maxtemp)
    if [ "$T" -ge "$HOT" ] && [ "$STATE" = "norm" ]; then
        setcap 1766400
        STATE=hot
    elif [ "$T" -le "$COOL" ] && [ "$STATE" = "hot" ]; then
        setcap 2073600
        STATE=norm
    fi
    sleep 2
done