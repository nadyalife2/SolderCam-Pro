#!/system/bin/sh
# Melvin Turbo Rick On-Device AI Stack (Helio X20 MT6797 • Nikel)
# Pure ext4 Native Execution + Bionic Host + PRoot Orchestrator

export PROOT_TMP_DIR=/data/local/tmp

echo "=== ОСТАНОВКА СТАРЫХ ПРОЦЕССОВ ==="
pkill -9 -f llama-server 2>/dev/null
pkill -9 -f python3 2>/dev/null
pkill -9 -f proot 2>/dev/null
sleep 2

echo "=== ЗАПУСК NATIVE LLAMA-SERVER (EXT4 • NO-MMAP • NO-PROOT) ==="
echo "Hardware: MT6797 Tri-Cluster (Cortex-A53 / A72)"
echo "Weights: Qwen2.5-0.5B-Instruct-Q4_0.gguf (Native NEON Interleaved)"

export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=4
export OMP_WAIT_POLICY=PASSIVE

# Запуск чистого нативного llama-server вне PRoot (без ptrace-оверхеда)
/data/local/tmp/melvin-bin/llama-server \
    -m /data/local/tmp/models/qwen2.5-0.5b-instruct-q4_0.gguf \
    -c 512 \
    -b 512 \
    -ub 256 \
    -t 4 \
    -tb 4 \
    -np 1 \
    -ctk f16 \
    -ctv f16 \
    -lm none \
    --host 127.0.0.1 \
    --port 8080 > /data/local/tmp/llama_server.log 2>&1 &

echo "Ожидание готовности LLM-сервера (порт 8080)..."
for i in $(seq 1 30); do
    if grep -q "listening on http" /data/local/tmp/llama_server.log 2>/dev/null; then
        echo "LLM-сервер успешно слушает на 127.0.0.1:8080!"
        break
    fi
    sleep 1
done

echo "=== НАСТРОЙКА СЕТИ, DNS И ТАЙМЗОНЫ ДЛЯ ALPINE PROOT ==="
DNS_IP=$(getprop net.dns1)
if [ -n "$DNS_IP" ]; then
    echo "nameserver $DNS_IP" > /data/local/tmp/alpine/etc/resolv.conf
fi
echo "nameserver 8.8.8.8" >> /data/local/tmp/alpine/etc/resolv.conf

# Вычисляем POSIX TZ из хоста Android для точного времени (CST-8, MSK-3 и т.д.)
OFFSET=$(/system/bin/date +%z 2>/dev/null)
SIGN=$(echo "$OFFSET" | cut -c1)
HOURS=$(echo "$OFFSET" | cut -c2-3 | sed 's/^0//')
TZ_ABBR=$(/system/bin/date +%Z 2>/dev/null)
if [ "$SIGN" = "+" ]; then
    POSIX_TZ="${TZ_ABBR}-${HOURS}"
else
    POSIX_TZ="${TZ_ABBR}+${HOURS}"
fi
echo "Синхронизация таймзоны хоста: $POSIX_TZ (Android offset: $OFFSET)"

echo "=== ЗАПУСК ФОНОВОГО МОСТА ФОНАРИКА (HOST BIONIC) ==="
rm -f /sdcard/melvin/torch_cmd 2>/dev/null
(
    while true; do
        if [ -f /sdcard/melvin/torch_cmd ]; then
            CMD=$(cat /sdcard/melvin/torch_cmd 2>/dev/null)
            rm -f /sdcard/melvin/torch_cmd
            if [ "$CMD" = "1" ]; then
                /system/bin/am broadcast -a miui.intent.action.TOGGLE_TORCH --ez miui.intent.extra.IS_ENABLE true >/dev/null 2>&1
            elif [ "$CMD" = "0" ]; then
                /system/bin/am broadcast -a miui.intent.action.TOGGLE_TORCH --ez miui.intent.extra.IS_ENABLE false >/dev/null 2>&1
            fi
        fi
        sleep 0.1
    done
) &

echo "=== ЗАПУСК ОРКЕСТРАТОРА (PYTHON3 • FLASK • FTS5 RAG) ==="
/data/local/tmp/proot -r /data/local/tmp/alpine -0 -b /dev -b /proc -b /sys -b /system -b /sdcard/melvin:/melvin /bin/busybox sh -c "
    export TZ='$POSIX_TZ'
    export PATH=/bin:/sbin:/usr/bin:/usr/sbin:/system/bin
    python3 /melvin/agent_orchestrator.py
"
