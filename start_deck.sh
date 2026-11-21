#!/data/data/com.termux/files/usr/bin/sh
# ==============================================================================
# Triad-Omni Hardware Deck Startup Script for Redmi Note 4 (NODE-3)
# ==============================================================================
termux-wake-lock
pgrep sshd >/dev/null || sshd

pkill -f "omni_fast_router" 2>/dev/null
pkill -f "omni_gateway" 2>/dev/null
sleep 1

# Launch Master Router in background
ROUTER_SCRIPT="$HOME/scripts/omni_fast_router_v4_9.py"
if [ ! -f "$ROUTER_SCRIPT" ]; then
    ROUTER_SCRIPT="$HOME/omni_fast_router_v4_9.py"
fi
if [ ! -f "$ROUTER_SCRIPT" ]; then
    ROUTER_SCRIPT="$HOME/omni_gateway.py"
fi

nohup python3 "$ROUTER_SCRIPT" > "$HOME/gateway.log" 2>&1 &
sleep 2

# Wake up screen and set optimal kiosk brightness
input keyevent 224
settings put system screen_brightness 38 2>/dev/null

# Open Hardware Deck Kiosk UI in Chrome
am start -n com.android.chrome/com.google.android.apps.chrome.Main -d "http://127.0.0.1:8000/?deck=1" --ez "create_new_tab" true 2>/dev/null
echo "Triad-Omni Deck Started on port 8000!"
