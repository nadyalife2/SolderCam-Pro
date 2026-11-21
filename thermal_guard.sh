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
    p="/sys/devices/system/cpu/cpufreq/policy6"
    if [ -d "$p" ]; then
        BEST=""
        for f in $(cat "$p/scaling_available_frequencies" 2>/dev/null); do
            [ "$f" -le "$1" ] && BEST=$f
        done
        [ -n "$BEST" ] && su -c "echo $BEST > $p/scaling_max_freq" 2>/dev/null
    fi
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