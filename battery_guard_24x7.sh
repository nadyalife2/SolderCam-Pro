#!/system/bin/sh
# Wrapper redirecting to scripts/battery_guard_24x7.sh
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$DIR/scripts/battery_guard_24x7.sh" ]; then
  exec "$DIR/scripts/battery_guard_24x7.sh" "$@"
fi
exec "$HOME/scripts/battery_guard_24x7.sh" "$@"
