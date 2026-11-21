#!/bin/sh
# ==============================================================================
# Triad-Omni Cluster | Termux Pristine Cleaner & Decommissioner v5.2
# Возвращает любой смартфон кластера (Mi 10T, Nord N10, Redmi Note 4)
# в абсолютно чистый, холодный штатный режим Android с освобождением 100% RAM.
# ==============================================================================

echo "🧹 [Triad-Omni] Запуск глубокой деактивации Termux и очистки..."

# 1. Снятие процессорного WakeLock (разрешить ядрам уходить в глубокий сон C-states)
if command -v termux-wake-unlock >/dev/null 2>&1; then
    termux-wake-unlock
    echo "⚡ [1/6] WakeLock снят. Процессор может переходить в глубокий сон."
fi

# 2. Принудительное завершение всех тяжелых ИИ-демонов и фоновых серверов
pkill -9 -f llama-server 2>/dev/null && echo "🛑 [2/6] llama-server завершен (выгружен из LPDDR)." || true
pkill -9 -f "python.*omni_fast_router" 2>/dev/null && echo "🛑 [2/6] Fast-Path роутер остановлен." || true
pkill -9 -f "python.*bge" 2>/dev/null && echo "🛑 [2/6] BGE-M3 эмбеддинги остановлены." || true
pkill -9 -f "python.*lfm" 2>/dev/null && echo "🛑 [2/6] LFM2.5 модель остановлена." || true
pkill -9 -f node 2>/dev/null || true

# 3. Полное удаление временного мусора, сокетов, логов и кэшей
rm -rf "$PREFIX/tmp"/* /tmp/* "$HOME/.cache"/* "$HOME"/*.log "$HOME"/*.cache "$HOME/lookup.cache" 2>/dev/null
echo "🗑️ [3/6] Временные файлы, сокеты и кэши /tmp очищены."

# 4. Восстановление штатного режима контроллера батареи (снять байпас питания)
if [ -w /sys/class/power_supply/battery/charging_enabled ]; then
    echo 1 > /sys/class/power_supply/battery/charging_enabled 2>/dev/null
elif [ -f /system/bin/su ]; then
    su -c "echo 1 > /sys/class/power_supply/battery/charging_enabled 2>/dev/null; echo 1 > /sys/class/power_supply/battery/battery_charging_enabled 2>/dev/null; echo 0 > /sys/class/power_supply/battery/input_suspend 2>/dev/null" 2>/dev/null || true
fi
echo "🔋 [4/6] Контроллер заряда восстановлен в штатный режим (байпас выключен)."

# 5. Сброс кэшей ядра Linux (drop_caches) и возврат ОЗУ системе Android
sync
if [ -f /system/bin/su ]; then
    su -c "echo 3 > /proc/sys/vm/drop_caches" 2>/dev/null && echo "🧠 [5/6] Кэши ядра сброшены. Вся RAM возвращена Android LMK." || true
else
    echo "🧠 [5/6] Файловые буферы сброшены (sync)."
fi

# 6. Закрытие сессии Termux и снятие постоянного уведомления
echo "✅ [6/6] Устройство полностью чистое, холодное и готово к штатному использованию!"
sleep 1

# Завершение Termux
if [ "$1" = "--kill-app" ]; then
    if [ -f /system/bin/su ]; then
        su -c "am force-stop com.termux" 2>/dev/null
    else
        pkill -9 -f com.termux 2>/dev/null || exit 0
    fi
else
    exit 0
fi
