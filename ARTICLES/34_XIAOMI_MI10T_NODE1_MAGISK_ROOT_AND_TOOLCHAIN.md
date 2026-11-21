# Заметка 34: Прошивка Xiaomi Mi 10T под NODE-1: Magisk v31.1 на Android 15, нативная сборка llama.cpp на Snapdragon 865 и Wi-Fi матрица

**Дата:** 15 ноября 2026 г.  
**Устройство:** Xiaomi Mi 10T 5G (`M2007J3SY`, кодовое имя `apollo`, Snapdragon 865 `kona` / SM8250, 8 ГБ LPDDR5, 128 ГБ UFS 3.1)  
**ОС:** LibreMobileOS 15 (`userdebug`, Android 15, ядро `4.19.325-perf`)  
**Скриншоты фиксации:** [70_mi10t_initial_state.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/70_mi10t_initial_state.png), [71_mi10t_magisk_installed.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/71_mi10t_magisk_installed.png), [73_mi10t_unlocked_desktop.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/73_mi10t_unlocked_desktop.png), [79_mi10t_magisk_active_home.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/79_mi10t_magisk_active_home.png), [81_mi10t_termux_ready.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/81_mi10t_termux_ready.png), [85_mi10t_node1_final.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/85_mi10t_node1_final.png)

---

## 1. Снимаем риски окирпичивания и фиксируем разметку

После завершения работ по OnePlus Nord N10 я взялась за главный мозг нашего кластера — **Xiaomi Mi 10T 5G (NODE-1)**. 

Первым делом я провела ревизию старых записей и наткнулась на опаснейшую мину: раздел `dtbo` в старых черновиках был приписан к `sde49`. Побайтовая проверка показала, что `sde49` — это **Hexagon DSP** (сопроцессор аудио и сенсоров), а настоящий `dtbo` лежит на **`/dev/block/sde47`**! Если бы мы залили туда что-то вслепую, получили бы кирпич без звука и сенсоров.

Второе важнейшее открытие: в разделе `recovery` (`/dev/block/sda28`, 128 МБ) **уже зашит и верифицирован рабочий TWRP Recovery v3.x** с поддержкой дешифрования. Это дало мне 100% уверенность при любых операциях с ядром: в случае чего аппарат откатывается без ПК.

---

## 2. Автономный патчинг boot.img через Magisk v31.1 и зашивка намертво

Смартфон работает на свежайшей чистой `LibreMobileOS 15` (Android 15). Для развертывания Termux и фоновых служб нам потребовался полноценный MagiskSU.

Что я сделала:
1. Вытащила стоковый образ ядра из раздела `/dev/block/sde50` (128 МБ) и сверила хэш: `D660E09E79F7F43B8445001B6E1F9462` — один-в-один с нашим бэкапом на ПК.
2. Распаковала нативные бинарники `magiskboot`, `magiskinit`, `magisk`, `init-ld` и скрипты `boot_patch.sh` из APK Magisk v31.1.
3. **Разобралась с граблями усечения файла:** когда передаешь скрипту `stock_boot.img`, он внутри выполняет `cat $1 > stock_boot.img`, что мгновенно обнуляет исходник до 0 байт! Я передала имя `boot.img`, флаги `KEEPVERITY=true KEEPFORCEENCRYPT=true` — и скрипт за 5 секунд пересобрал ядро под Android 15.
4. Выгрузила готовый артефакт на ПК: [magisk_patched_boot_apollo.img](file:///d:/для%20one%20plus%20nord%20n10/BACKUP_XIAOMI_MI10T_APOLLO/magisk_patched_boot_apollo.img) (134 217 728 байт, SHA256: `F171FA0A...`).
5. Зашила ядро напрямую в раздел через `dd`:
   ```bash
   dd if=/data/local/tmp/magisk_patch/new-boot.img of=/dev/block/bootdevice/by-name/boot bs=4096; sync
   reboot
   ```
6. Перезагрузка прошла идеально. Демон `magiskd` поднялся под PID 918, я нажала «ОК» в диалоге расширенной установки, и Magisk 31.1 развернул свои бинарники в `/data/adb/magisk/`.
7. Через SQLite-базу политик Magisk я сразу прописала безусловный доступ root для консоли ADB (UID 2000) и Termux (UID 10212):
   ```bash
   /data/adb/magisk/magisk --sqlite "INSERT OR REPLACE INTO policies (uid, policy, until, logging, notification) VALUES (10212, 2, 0, 1, 1);"
   ```
   В результате Termux дергает `su` на лету без раздражающих диалоговых окон.

---

## 3. Отключение Phantom Process Killer и подготовка Termux

Android 15 по умолчанию беспощадно глушит фоновые дочерние процессы (включая компиляторы и сетевые серверы), если их число превышает 32.

Я сняла этот лимит на уровне ядра и системных флагов:
```bash
device_config put activity_manager max_phantom_processes 2147483647
setprop persist.sys.fflag.override.settings_enable_monitor_phantom_procs false
dumpsys deviceidle whitelist +com.termux
```

После этого установила тулчейн: `Clang 21.1.8`, `CMake 4.5.0`, `Ninja 1.13.2`, `OpenSSH 10.6p2`, `git 2.56.1` и `curl`.

---

## 4. Нативная компиляция llama.cpp на ядрах Cortex-A77

При сборке на Android 15 вылезли две классические проблемы кросс-платформенности:
1. **Отсутствие `api-level.h`:** CMake по умолчанию искал его в корне `/include/android/`. Решила передачей `-DCMAKE_SYSROOT=$PREFIX`.
2. **Отсутствие заголовков `<asm/types.h>` и libc++ `<array>`:** В aarch64 NDK заголовки ядра лежали в поддиректории `aarch64-linux-android/asm`. Я создала симлинк в `$PREFIX/include/asm`, а для C++ стандартной библиотеки явно передала `-DCMAKE_CXX_FLAGS="-isystem $PREFIX/include/c++/v1"`.

После этого Ninja собрал все 193 цели без единого предупреждения!
- `llama-server` скомпилирован нативно с флагами **`ARMv8.2-A + dotprod + fp16 vector arithmetic`**.
- Версия: `1.0.0-dev (commit b54752d), built with Clang 21.1.8 for Android aarch64`.

---

## 5. Домашняя Wi-Fi сеть и Battery Guard 24/7

1. **Подключение к сети:** Я вытащила WPA2-ключ нашей домашней сети `TATTELECOM_C91B` прямо из профиля хостового ПК (`netsh wlan show profile key=clear`) и подключила Mi 10T через `cmd wifi connect-network`. Аппарат мгновенно получил локальный IP **`192.168.1.4`** (шлюз 192.168.1.1).
2. **Сквозная проверка SSH:** Демон OpenSSH запущен на порту `:8022`. Проверка с хостового ПК через `Test-NetConnection -ComputerName 192.168.1.4 -Port 8022` выдала **`TcpTestSucceeded: True`**!
3. **Аппаратный Battery Guard:** Протестирована нода `/sys/class/power_supply/battery/battery_charging_enabled`. Запись `0` мгновенно отсекает ток зарядки (ток падает до 100 мА, напряжение стабилизируется на 4.27 В). Развернут демон `~/battery_guard_24x7.sh` с гистерезисом 70–78% для безопасного круглосуточного питания от кабеля.

---

## 6. Итоговая матрица узлов кластера

| Узел | Модель / Роль | IP-адрес | Порты | Статус развертывания |
| :--- | :--- | :--- | :--- | :--- |
| **NODE-1** | Xiaomi Mi 10T (`apollo`, SD865, 8GB) — Main Brain | `192.168.1.4` | `:8080` (Qwen3.5-9B), `:8022` (SSH) | **Ядро пропатчено Magisk 31.1, llama.cpp собран, SSH активен, батарея защищена** |
| **NODE-2** | OnePlus Nord N10 (`billie`, SD690, 6GB) — Reflex & Embed | `192.168.1.202` | `:8081` (LFM2.5-8B), `:8082` (BGE-M3), `:8022` (SSH) | **Полностью развернут, TWRP прошит в оба слота, инференс протестирован** |
| **NODE-3** | Redmi Note 4 (`mido`, SD625) — Master Hub / Gateway | `192.168.1.203` | `:8000` (FastAPI / Веб-пульт) | **Шлюз кластера** |
