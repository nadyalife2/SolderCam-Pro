#!/usr/bin/env bash
# ==============================================================================
# Triad-Omni Environment Loader (v5.1)
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$DIR/config/cluster.env"

if [ -f "$ENV_FILE" ]; then
    # Export all variables from cluster.env
    set -a
    source "$ENV_FILE"
    set +a
else
    export OMNI_TOKEN="sk-triad"
    export HUB_URL="http://192.168.31.48:8000"
    export NODE1_IP="192.168.31.161"
    export NODE1_URL="http://192.168.31.161:8080"
    export NODE2_IP="192.168.31.57"
    export NODE2_LFM="http://192.168.31.57:8081"
    export NODE3_IP="192.168.31.48"
    export NODE3_URL="http://192.168.31.48:8000"
fi

export PORT="${PORT:-8000}"
export SECONDARY_PORT="${SECONDARY_PORT:-5000}"
export LLAMA="${LLAMA:-$HOME/llama.cpp/build/bin/llama-server}"
export LD_LIBRARY_PATH="$HOME/llama.cpp/build/bin:/data/data/com.termux/files/usr/lib:$LD_LIBRARY_PATH"
export PATH="$HOME/llama.cpp/build/bin:/data/data/com.termux/files/usr/bin:$PATH"
