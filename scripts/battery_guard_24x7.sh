#!/data/data/com.termux/files/usr/bin/sh
# ==============================================================================
# Triad-Omni 24/7 Battery Guard & Hardware Bypass Manager
# Works across Qualcomm (PM8150B, PM7250B, PMI8952) and MediaTek PMICs.
# Keeps battery charged between 70% and 78% during 24/7 AI cluster duty.
# Prevents lithium pouch swelling and thermal degradation.
# ==============================================================================

export HOME="/data/data/com.termux/files/home"

# Auto-detect charging control sysfs node
if [ -f "/sys/class/power_supply/battery/charging_enabled" ]; then
  CHG_NODE="/sys/class/power_supply/battery/charging_enabled"
elif [ -f "/sys/class/power_supply/battery/battery_charging_enabled" ]; then
  CHG_NODE="/sys/class/power_supply/battery/battery_charging_enabled"
elif [ -f "/sys/class/power_supply/battery/input_suspend" ]; then
  CHG_NODE="/sys/class/power_supply/battery/input_suspend"
else
  CHG_NODE="/sys/class/power_supply/battery/charging_enabled"
fi

MAX_CAP=78
MIN_CAP=70
CYCLE_COUNT=0

set_charging() {
  val="$1"
  if [ "$(id -u)" -eq 0 ] || [ -w "$CHG_NODE" ]; then
    echo "$val" > "$CHG_NODE" 2>/dev/null
  else
    echo "$val" | su -c "tee $CHG_NODE" > /dev/null 2>&1
  fi
}

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 24/7 Battery Guard service started (node: $CHG_NODE)"

while true; do
  CAP=$(cat /sys/class/power_supply/battery/capacity 2>/dev/null || su -c "cat /sys/class/power_supply/battery/capacity" 2>/dev/null || echo 100)
  CHG_EN=$(cat "$CHG_NODE" 2>/dev/null || su -c "cat $CHG_NODE" 2>/dev/null || echo 1)
  TEMP_RAW=$(cat /sys/class/power_supply/battery/temp 2>/dev/null || su -c "cat /sys/class/power_supply/battery/temp" 2>/dev/null || echo 0)
  TEMP_C=$(awk -v t="$TEMP_RAW" 'BEGIN{printf "%.1f", t/10}')

  if [ "$CAP" -ge "$MAX_CAP" ] && [ "$CHG_EN" -eq 1 ]; then
    set_charging 0
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Battery at $CAP% >= $MAX_CAP%: Charging disabled (Bypass mode active, Temp: ${TEMP_C}°C)"
  elif [ "$CAP" -le "$MIN_CAP" ] && [ "$CHG_EN" -eq 0 ]; then
    set_charging 1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Battery at $CAP% <= $MIN_CAP%: Charging enabled (Recharge mode, Temp: ${TEMP_C}°C)"
  fi

  CYCLE_COUNT=$((CYCLE_COUNT + 1))
  # Heartbeat log every ~5 minutes (15 cycles * 20s)
  if [ "$CYCLE_COUNT" -ge 15 ]; then
    CYCLE_COUNT=0
    STATUS_STR="Bypass mode (charging disabled)"
    [ "$CHG_EN" -eq 1 ] && STATUS_STR="Recharging (charging enabled)"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [HEARTBEAT] Battery: $CAP%, Temp: ${TEMP_C}°C, State: $STATUS_STR"
  fi

  sleep 20
done
