#!/data/data/com.termux/files/usr/bin/sh
. "$HOME/omni_env.sh"
NODE_ID="${1:-nord10}"

CAP=$(cat /sys/class/power_supply/battery/capacity 2>/dev/null || echo 0)
BT=$(cat /sys/class/power_supply/battery/temp 2>/dev/null || echo 0)
SOC=0
for z in /sys/class/thermal/thermal_zone*; do
    case "$(cat "$z/type" 2>/dev/null)" in
      *cpu*|*soc*|*tsens*|*apc*|*gpuss*) V=$(cat "$z/temp" 2>/dev/null || echo 0)
         [ "$V" -gt "$SOC" ] 2>/dev/null && SOC=$V ;;
    esac
done
TEMP=$(awk -v s="$SOC" -v b="$BT" 'BEGIN{s=s/1000;b=b/10;print (s>b)?s:b}')
RAM=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)
MAC=$(cat /sys/class/net/wlan0/address 2>/dev/null || echo "00:00:00:00:00:00")
PROF=$(cat "$HOME/current_profile.txt" 2>/dev/null || echo reflex)

echo "{\"node\":\"$NODE_ID\",\"battery\":$CAP,\"temp_c\":$TEMP,\"free_ram_mb\":$RAM,\"mac\":\"$MAC\",\"profile\":\"$PROF\"}"