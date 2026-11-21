# 01. Сеть, Прошивки и Вычислительные Узлы (NODE-1 & NODE-2)

> Архитектура Triad-Omni v4.7: конвейерная гетерогенная система.  
> Главный принцип: **один узел = одна модель**, по сети передаётся только чистый JSON. RPC по Wi-Fi полностью удалён.

---

## 1. Сетевая матрица и настройка роутера (Wi-Fi 5 ГГц)

Для исключения сетевых задержек и jitter при передаче контекстов:
1. Разделите диапазоны 2.4 ГГц и 5 ГГц (отключите *Smart Connect*). Зафиксируйте для 5 ГГц канал `36` или `44` (ширина `80 МГц`).
2. На всех смартфонах в свойствах Wi-Fi сети установите: **Конфиденциальность -> Использовать MAC-адрес устройства (заводской)**.
3. В роутере (*LAN -> DHCP Static Lease*) жестко зафиксируйте статические IP:

| Узел | Устройство | SoC / ОЗУ | IP-адрес | Порты | Модель / Назначение |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NODE-1** | Xiaomi Mi 10T (`apollo`) | SD865 / 8GB LPDDR5 | `192.168.1.201` | `:8080` (LLM/Vision), `:8022` (SSH) | **Qwen3.5-9B-MTP UD-Q3_K_XL** (текст) + 3 слота LoRA (`solder`, `reva_android`, `esp32`); зрение — **Gemma 4 E4B** (LRU-вытеснение) |
| **NODE-2** | OnePlus Nord N10 (`billie`) | SD690 / 6GB LPDDR4X | `192.168.1.202` | `:8081` (Reflex), `:8082` (BGE-M3), `:8022` (SSH) | **LFM2.5-8B-A1B IQ3_XXS** (роутер/классификатор/small-fast) на 2×A77 + **BGE-M3** (эмбеддинги) на 6×A55 |
| **NODE-3** | Redmi Note 4 (`nikel`) | Helio X20 / 3GB LPDDR3 | `192.168.1.203` | `:8000` (Hub/Web UI/API), `:8022` (SSH) | Шлюз, база знаний SQLite FTS5 на `/data`, каскад эскалации `/v1/escalate`, Claude Code SSE/tools |
| **NODE-4** | ПК (Ubuntu 22.04 LTS) | 16GB RAM + GTX 1050 Ti (4GB) | `192.168.1.100` | `:8090` (Teacher MoE), `:22` (SSH) | **Qwen3-Coder-30B-A3B-Instruct IQ3_XS** (CPU offload экспертов), куратор датасетов, хук компилятора |

> [!IMPORTANT]
> **RPC по Wi-Fi удалён навсегда.** Передача 12 ГБ тензоров по беспроводной сети давала задержки 400–900 мс на токен и приводила к зависаниям при дропах пакетов. Теперь каждый узел автономен.

---

## 2. Единый конфигурационный файл `~/omni_env.sh`

Создаётся на всех узлах (права доступа `600`):

```sh
# ~/omni_env.sh — единый источник токена и адресов кластера
export OMNI_TOKEN="СМЕНИ_НА_ДЛИННЫЙ_СЛУЧАЙНЫЙ_ТОКЕН_ХЭШ"
export HUB_URL="http://192.168.1.203:8000"
export HUB_IP="192.168.1.203"
export MI10T_IP="192.168.1.201"
export NORD_IP="192.168.1.202"
export PC_IP="192.168.1.100"
export LLAMA="$HOME/llama.cpp/build/bin/llama-server"
```

Команда установки прав:
```sh
chmod 600 ~/omni_env.sh
pkg update -y && pkg install -y curl iw rsync openssh
```

---

## 3. Сборка llama.cpp в Termux (без RPC и без лишнего OpenMP оверхеда)

На Mi 10T и Nord N10:
```sh
cd ~
git clone --depth 1 https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -G Ninja -DGGML_OPENMP=OFF -DGGML_RPC=OFF
cmake --build build -j6
```

---

## 4. NODE-1 (Xiaomi Mi 10T, 8GB): Главный мозг

### 4.1. Скачивание квантованных моделей
```sh
pkg install -y python python-pip
pip install -U huggingface_hub
mkdir -p ~/models ~/adapters ~/models/dl

# Скачивание текстового мозга с поддержкой MTP (Multi-Token Prediction)
hf download unsloth/Qwen3.5-9B-MTP-GGUF --include "*UD-Q3_K_XL*" --local-dir ~/models/dl
# Скачивание нативной мультимодальной модели зрения (Gemma 4 E4B + mmproj)
hf download ggml-org/gemma-4-E4B-it-GGUF --include "*Q4_K_M*" --include "*mmproj-F16*" --local-dir ~/models/dl

mv ~/models/dl/*UD-Q3_K_XL*.gguf ~/models/brain.gguf
mv ~/models/dl/*q4_k_m*.gguf   ~/models/gemma4-e4b.gguf
mv ~/models/dl/*mmproj*.gguf   ~/models/gemma4-e4b-mmproj.gguf
rm -rf ~/models/dl
```

**Бюджет памяти Mi 10T (8 ГБ LPDDR5):**
- Текстовый мозг `UD-Q3_K_XL`: 5.05 ГБ
- MTP драфт-голова: ~0.40 ГБ
- KV-кэш 16K (`q8_0`): ~0.35 ГБ
- Lora-адаптеры (3 шт.) + буферы активаций: ~0.50 ГБ
- **Итого:** ~6.30 ГБ. При свободной системной памяти 7.1 ГБ (после гашения UI) остаётся стабильный запас 800 МБ без риска OOM.

### 4.2. Скрипт запуска `~/start_brain.sh`
Поддерживает горячие режимы: `router | plain | vision | stop | status`.

```sh
#!/data/data/com.termux/files/usr/bin/sh
# Использование: ~/start_brain.sh [router|plain|vision|stop|status]
. "$HOME/omni_env.sh"
MODE="${1:-router}"
LOG="$HOME/brain.log"
mkdir -p "$HOME/models" "$HOME/adapters" "$HOME/.termux/boot"

hard_setup() {
    pgrep sshd >/dev/null || sshd
    su -c "stop surfaceflinger && stop zygote" 2>/dev/null
    su -c "echo 0 > /sys/class/leds/lcd-backlight/brightness" 2>/dev/null
    # КРИТИЧНО: после остановки zygote framework-wakelock'и освобождены
    su -c "echo omni_brain > /sys/power/wake_lock" 2>/dev/null
    su -c "iw dev wlan0 set power_save off" 2>/dev/null
    su -c "ip addr add 192.168.1.201/24 dev wlan0" 2>/dev/null
    # Ограничение частоты до 2.22 ГГц для снижения тепловыделения на 35%
    su -c "echo 2227200 > /sys/devices/system/cpu/cpufreq/policy4/scaling_max_freq" 2>/dev/null
    su -c "echo 2227200 > /sys/devices/system/cpu/cpufreq/policy7/scaling_max_freq" 2>/dev/null
}

stop_all() {
    pkill -f brain_watchdog.sh 2>/dev/null
    pkill -f "llama-server" 2>/dev/null
    i=0; while pgrep -f "llama-server" >/dev/null && [ $i -lt 20 ]; do sleep 0.5; i=$((i+1)); done
}

case "$MODE" in
  stop)   stop_all; echo "stopped"; exit 0 ;;
  status) pgrep -af llama-server || echo "no server"; exit 0 ;;
esac

hard_setup
stop_all
echo "$MODE" > "$HOME/current_profile.txt"

# Генерация пресетов с абсолютными путями (llama-server router не раскрывает ~)
cat > "$HOME/brain.ini" <<EOF
[brain]
model = $HOME/models/brain.gguf
ctx-size = 16384
lora = $HOME/adapters/lora_9b_solder.gguf,$HOME/adapters/lora_9b_reva.gguf,$HOME/adapters/lora_9b_esp32.gguf
spec-type = draft-mtp
spec-draft-n-max = 2
n-parallel = 1
cache-reuse = 256
temp = 0.7
top-p = 0.8

[vision]
model = $HOME/models/gemma4-e4b.gguf
mmproj = $HOME/models/gemma4-e4b-mmproj.gguf
ctx-size = 32768
n-parallel = 1
cache-reuse = 256
temp = 0.7
top-p = 0.8
EOF

# Watchdog с backoff, ротацией лога и проверкой сети
cat > "$HOME/brain_watchdog.sh" <<'WDOG'
#!/data/data/com.termux/files/usr/bin/sh
. "$HOME/omni_env.sh"
LOG="$HOME/brain.log"; FAILS=0; NETFAIL=0
while true; do
    MODE=$(cat "$HOME/current_profile.txt" 2>/dev/null || echo router)
    [ "$(stat -c%s "$LOG" 2>/dev/null || echo 0)" -gt 5000000 ] && \
        tail -c 500000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"

    echo "[$(date)] start mode=$MODE" >> "$LOG"
    if [ "$MODE" = "router" ]; then
        taskset -c 4,5,6,7 "$LLAMA" \
          --models-dir "$HOME/models" --models-preset "$HOME/brain.ini" --models-max 1 \
          -t 4 -tb 4 -ctk q8_0 -ctv q8_0 --flash-attn --jinja \
          --host 0.0.0.0 --port 8080 >> "$LOG" 2>&1
    elif [ "$MODE" = "vision" ]; then
        taskset -c 4,5,6,7 "$LLAMA" -m "$HOME/models/gemma4-e4b.gguf" \
          --mmproj "$HOME/models/gemma4-e4b-mmproj.gguf" \
          -c 32768 -t 4 -tb 4 -ctk q8_0 -ctv q8_0 --flash-attn --jinja \
          -np 1 --cache-reuse 256 --host 0.0.0.0 --port 8080 >> "$LOG" 2>&1
    else
        taskset -c 4,5,6,7 "$LLAMA" -m "$HOME/models/brain.gguf" \
          --lora "$HOME/adapters/lora_9b_solder.gguf,$HOME/adapters/lora_9b_reva.gguf,$HOME/adapters/lora_9b_esp32.gguf" \
          -c 16384 -t 4 -tb 4 -ctk q8_0 -ctv q8_0 --flash-attn --jinja \
          --spec-type draft-mtp --spec-draft-n-max 2 \
          -np 1 --cache-reuse 256 --host 0.0.0.0 --port 8080 >> "$LOG" 2>&1
    fi

    FAILS=$((FAILS+1)); S=$((FAILS*5)); [ $S -gt 60 ] && S=60
    echo "[$(date)] server exited, backoff ${S}s" >> "$LOG"; sleep $S

    if ! ping -c1 -W2 "$HUB_IP" >/dev/null 2>&1; then
        NETFAIL=$((NETFAIL+1))
        [ $NETFAIL -ge 6 ] && su -c "ip link set wlan0 down; sleep 2; ip link set wlan0 up" && NETFAIL=0
    else
        NETFAIL=0; FAILS=0
    fi
done
WDOG
chmod +x "$HOME/brain_watchdog.sh"
nohup "$HOME/brain_watchdog.sh" >/dev/null 2>&1 &

pgrep -f thermal_guard.sh   >/dev/null || nohup "$HOME/thermal_guard.sh"   >/dev/null 2>&1 &
pgrep -f node_telemetry.sh  >/dev/null || nohup "$HOME/node_telemetry.sh" mi10t >/dev/null 2>&1 &
echo "✅ brain запущен в режиме [$MODE]"
```

### 4.3. Термогвард `~/thermal_guard.sh`
Проверяет температуру каждые 2 секунды. При превышении 47 °C снижает лимит частоты CPU до 1.8 ГГц; при остывании до 43 °C возвращает 2.22 ГГц.

```sh
#!/data/data/com.termux/files/usr/bin/sh
HOT=47000; COOL=43000; STATE=norm
maxtemp() {
    M=0
    for z in /sys/class/thermal/thermal_zone*; do
        case "$(cat "$z/type" 2>/dev/null)" in
          *cpu*|*soc*|*tsens*|*apc*) V=$(cat "$z/temp" 2>/dev/null || echo 0)
             [ "$V" -gt "$M" ] 2>/dev/null && M=$V ;;
        esac
    done
    echo "$M"
}
setcap() {
    for p in /sys/devices/system/cpu/cpufreq/policy4 /sys/devices/system/cpu/cpufreq/policy7; do
        [ -d "$p" ] || continue
        BEST=""
        for f in $(cat "$p/scaling_available_frequencies" 2>/dev/null); do
            [ "$f" -le "$1" ] && BEST=$f
        done
        [ -n "$BEST" ] && su -c "echo $BEST > $p/scaling_max_freq" 2>/dev/null
    done
}
while true; do
    T=$(maxtemp)
    if [ "$T" -ge "$HOT" ] && [ "$STATE" = norm ]; then setcap 1804800; STATE=hot
    elif [ "$T" -le "$COOL" ] && [ "$STATE" = hot ]; then setcap 2227200; STATE=norm; fi
    sleep 2
done
```

---

## 5. NODE-2 (OnePlus Nord N10, 6GB): Reflex & Векторный Движок

### 5.1. Скачивание моделей для Nord N10
```sh
pip install -U huggingface_hub
mkdir -p ~/models ~/models/dl
hf download LiquidCloud/LFM2.5-8B-A1B-GGUF --include "*IQ3_XXS*" --local-dir ~/models/dl
hf download ggml-org/bge-m3-GGUF --include "*bge-m3*" --local-dir ~/models/dl

mv ~/models/dl/*IQ3_XXS*.gguf ~/models/lfm25-8b-a1b-iq3xxs.gguf
mv ~/models/dl/*bge-m3*.gguf ~/models/bge-m3.gguf
rm -rf ~/models/dl
```

### 5.2. Скрипт запуска `~/.termux/boot/start_reflex.sh`
Разносит нагрузку по ядрам:
- 2 быстрых ядра A77 (cores 6,7) обслуживают порт `:8081` (Reflex LLM).
- 6 энергоэффективных ядер A55 (cores 0-5) обслуживают порт `:8082` (BGE-M3 эмбеддинги).

```sh
#!/data/data/com.termux/files/usr/bin/sh
. "$HOME/omni_env.sh"
termux-wake-lock 2>/dev/null
su -c "echo omni_reflex > /sys/power/wake_lock" 2>/dev/null
su -c "iw dev wlan0 set power_save off" 2>/dev/null
pgrep sshd >/dev/null || sshd
pkill -f llama-server 2>/dev/null; sleep 2

# :8081 — LFM2.5-8B-A1B (роутер/классификатор/small-fast), 2 ядра A77
nohup taskset -c 6,7 "$LLAMA" -m "$HOME/models/lfm25-8b-a1b-iq3xxs.gguf" --jinja \
  -c 8192 -t 2 -tb 2 -ctk q8_0 -ctv q8_0 --flash-attn \
  -np 1 --host 0.0.0.0 --port 8081 > "$HOME/reflex.log" 2>&1 &

# :8082 — BGE-M3, 6 ядер A55
nohup taskset -c 0,1,2,3,4,5 "$LLAMA" -m "$HOME/models/bge-m3.gguf" \
  --embedding --pooling cls -c 2048 -t 4 \
  --host 0.0.0.0 --port 8082 > "$HOME/embed.log" 2>&1 &

pgrep -f node_telemetry.sh >/dev/null || nohup "$HOME/node_telemetry.sh" nord10 >/dev/null 2>&1 &
```

---

## 6. Push-телеметрия `~/node_telemetry.sh` (Mi 10T и Nord N10)

Узлы самостоятельно пушат метрики на шлюз раз в 10 секунд (вместо SSH-pull, блокирующего потоки):

```sh
#!/data/data/com.termux/files/usr/bin/sh
. "$HOME/omni_env.sh"
NODE_ID="${1:-mi10t}"
while true; do
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
    PROF=$(cat "$HOME/current_profile.txt" 2>/dev/null || echo brain)
    curl -s -m 5 -X POST "$HUB_URL/api/telemetry" \
      -H "Content-Type: application/json" -H "X-Omni-Token: $OMNI_TOKEN" \
      -d "{\"node\":\"$NODE_ID\",\"battery\":$CAP,\"temp_c\":$TEMP,\"free_ram_mb\":$RAM,\"mac\":\"$MAC\",\"profile\":\"$PROF\"}" \
      >/dev/null 2>&1
    sleep 10
done
```

---

## 7. Скрипт предстартовой проверки `~/preflight.sh`

```sh
#!/data/data/com.termux/files/usr/bin/sh
. "$HOME/omni_env.sh"; B="http://127.0.0.1:8080"
echo "1) модели роутера:";      curl -s "$B/models" | head -c 400; echo
echo "2) LoRA видны (ждем 3):"; curl -s "$B/lora-adapters"; echo
echo "3) смена scale:";         curl -s -X POST "$B/lora-adapters" \
   -d '[{"id":0,"scale":1.0},{"id":1,"scale":0.0},{"id":2,"scale":0.0}]'; echo
echo "4) erase слота:";         curl -s -X POST "$B/slots/0?action=erase"; echo
echo "5) чат brain:";           curl -s "$B/v1/chat/completions" -H 'Content-Type: application/json' \
   -d '{"model":"brain","messages":[{"role":"user","content":"2+2=?"}],"max_tokens":16}' | head -c 300; echo
echo "6) чат vision (вытеснит brain):"; curl -s "$B/v1/chat/completions" -H 'Content-Type: application/json' \
   -d '{"model":"vision","messages":[{"role":"user","content":"ok"}],"max_tokens":8}' | head -c 300; echo
echo "--- лог: ищите ошибки тензоров LoRA и строки MTP/draft ---"
grep -iE "lora|draft|spec|error|failed" "$HOME/brain.log" | tail -30
```
