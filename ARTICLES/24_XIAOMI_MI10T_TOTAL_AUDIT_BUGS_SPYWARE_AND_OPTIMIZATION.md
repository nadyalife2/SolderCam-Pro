# Часть 24: Тотальный аудит Xiaomi Mi 10T — фатальный краш ядра в IIO, китайские шпионы SOTER и скрытый потенциал ART/ZRAM

> **В предыдущих сериях:** Мы намертво заглушили ультразвуковой визг в разговорном динамике через микшеры ALSA, по косточкам разобрали зависание шины Geni I2C контроллера PM8008 и сняли полный побитовый бэкап EFS, Persist и всех загрузочных разделов.  
> Теперь пришло время заглянуть под капот LibreMobileOS 15 на ядре 4.19.325: проверить, какие баги скрываются в логах, кто втихаря жрет память, какие службы шпионят за устройством и как выжать из флагманского Snapdragon 865 максимум скорости.

---

## 1. Фатальная мина в ядре: Как чтение датчика роняет ядро в Kernel Panic

Когда я полезла проверять, почему в логах каждые 8 секунд всплывает ошибка датчиков:
```text
11-14 15:09:09.776  1148  1223 E android.hardware.sensors@1.0-service: ERROR: Fix ultrasound sensor so it does not return error from poll()
```
я решила проверить системный интерфейс IIO (Industrial I/O), к которому привязан ультразвуковой датчик приближения Xiaomi Mi 10T (`apollo`).

В дереве устройств датчик зарегистрирован как драйвер платформы:
`/sys/bus/platform/drivers/us_prox/us_prox.0` $\rightarrow$ `/sys/bus/iio/devices/iio:device3` (`distance`).

Среди его атрибутов лежат стандартные узлы IIO:
- `current_timestamp_clock`
- `in_proximity_sampling_frequency`
- `in_proximity_raw`

Стоило мне выполнить невинную команду:
```bash
cat /sys/devices/platform/us_prox.0/iio:device3/in_proximity_raw
```
как телефон мгновенно ушел в жесткую перезагрузку (Warm Reset)!

Подняв дамп из энергонезависимой памяти `pstore` (`/sys/fs/pstore/console-ramoops-0`), я увидела классическую картину кривого китайского драйвера:

```text
[  764.313999] Unable to handle kernel NULL pointer dereference at virtual address 0000000000000000
[  764.314017] Mem abort info:
[  764.314022]   ESR = 0x86000005
[  764.314028]   Exception class = IABT (current EL), IL = 32 bits
[  764.314060] Internal error: Oops: 86000005 [#1] PREEMPT SMP
[  764.314079] Process cat (pid: 4730)
[  764.314103] pc :           (null)
[  764.314121] lr : iio_read_channel_info+0xa4/0xe8
[  764.314211] Call trace:
[  764.314215]            (null)
[  764.314319] Kernel panic - not syncing: Fatal exception
```

### Разбор полетов
Ядро Linux в подсистеме IIO при обращении к `in_proximity_raw` вызывает стандартную функцию `iio_read_channel_info`. Она извлекает структуру `indio_dev->info` и пытается дернуть указатель на метод:
```c
ret = indio_dev->info->read_raw(indio_dev, chan, &val, &val2, mask);
```
Но разработчики вендорного драйвера `us_prox` просто **забыли инициализировать указатель `read_raw`** (он равен `NULL`)!  
Процессор пытается прыгнуть по адресу `0x0000000000000000`, ловит аппаратное прерывание `IABT` (Instruction Abort) с кодом ошибки `86000005`, и ядро падает в немедленный Kernel Panic!

Именно поэтому HAL датчиков `android.hardware.sensors@1.0-service` (библиотека `sensors.mius.proximity.so`) не может получить адекватный ответ от устройства и бесконечно спамит в лог:  
`ERROR: Fix ultrasound sensor so it does not return error from poll()`.

Решение для полной стабильности:
1. Отвязать сбойный драйвер через sysfs: `echo "us_prox.0" > /sys/bus/platform/drivers/us_prox/unbind`.
2. Либо в кастомном ядре пропатчить структуру `us_prox_iio_info`, добавив валидную заглушку `read_raw`, возвращающую `-EINVAL` вместо прыжка в космос.

---

## 2. Спам батарейного контроллера и призрачный PM8009

В логах `dmesg` и `logcat` обнаружились еще две повторяющиеся аномалии:

### 1. Спам `fg_psy_get_property` каждые 4 секунды
```text
FG: fg_psy_get_property: unsupported property 67
FG: fg_psy_get_property: unsupported property 4
Get prop 67 is not supported in pc_port
healthd: battery l=83 v=4211 t=30.5 h=2 st=2 c=-293456 fc=4031000 cc=0 chg=u
```
Android 15 (HAL `android.hardware.health-service` / `healthd`) запрашивает свойства питания:
- Свойство `4` (`POWER_SUPPLY_PROP_ONLINE`)
- Свойство `67` (`POWER_SUPPLY_PROP_CHARGE_CONTROL_LIMIT_MAX` в новых стандартах AOSP).

Драйвер топливомера Qualcomm PM8150B (`fg_psy`) в ядре 4.19 не знает про свойство 67 и засыпает dmesg ошибками. На работу зарядки это не влияет (ток -293 мА при 4.2 В идет штатно), но засоряет буфер логов.

### 2. Призрачный чип PM8009 на шине SPMI
При загрузке ядра в dmesg выскакивает пачка ошибок:
```text
[ 0.383999] spmi spmi-0: pmic_arb_wait_for_done: transaction failed (0x3)
[ 0.384005] qcom,qpnp-power-on c440000.qcom,spmi:qcom,pm8009@a:qcom,power-on@800: Register read failed, addr=0x0805, rc=-5
[ 0.482185] spmi spmi-0: pmic_arb_wait_for_done: transaction failed (0x3)
[ 0.482199] qcom,qpnp-revid: probe of c440000.qcom,spmi:qcom,pm8009@a:revid@100 failed with error -22
```
В эталонной платформе Qualcomm Kona чип PM8009 висит на адресе SPMI `0xa`. В Xiaomi Mi 10T этой микросхемы физически нет на плате! Дерево устройств DTB скопировали с референса, поэтому ядро честно пытается опросить несуществующий чип, получает таймаут арбитра SPMI и отваливается. Ошибки чисто косметические.

---

## 3. Ревизия шпионских служб и мусора: Кто жрет оперативку?

Я провела полный аудит установленных пакетов (`pm list packages -u -f`), запущенных демонов (`ps -A`) и реального среза оперативной памяти по PSS (`dumpsys meminfo`):

### Настоящий пожиратель памяти на полгигабайта:
Главным пожирателем RAM оказался не сторонний софт, а **`com.libremobileos.dynamicwallpaper`** (PID 2430)!
Он съедает **от 213 до 418 МБ PSS**, удерживая **207 МБ dirty native heap** под текстуры живых обоев в видеопамяти. Смена живых обоев на статичные сразу освобождает почти 400 МБ быстрой LPDDR5!

### Банда скрытых вендорных и телеметрических служб:
| Процесс / Пакет | Путь к APK / Бинарнику | Реальный PSS | Что это такое и зачем оно здесь |
| :--- | :--- | :--- | :--- |
| **`com.tencent.soter.soterserver`** | `/vendor/app/SoterService/SoterService.apk` | 5.2 МБ (105 МБ RSS) | Китайский шлюз биометрических платежей WeChat/Tencent SOTER. Работает с демоном `vendor.qti.hardware.soter@1.0-service` (PID 1231). |
| **`org.ifaa.aidl.manager`** | `/system_ext/app/IFAAService/IFAAService.apk` | 6.0 МБ | Второй китайский биометрический шлюз IFAA (Alibaba / Alipay). |
| **`com.libremobileos.stats`** | `/system_ext/priv-app/LMOStats/LMOStats.apk` | 10.2 МБ (66 МБ RSS) | Встроенный телеметрический сборщик статистики LibreMobileOS. Периодически просыпается и шлет отчеты. |
| **`com.android.devicediagnostics`** | `/system_ext/priv-app/DeviceDiagnostics/DeviceDiagnostics.apk` | 11.6 МБ (63 МБ RSS) | Диагностический сервис для сбора дампов и отчетов об ошибках. |
| **Privacy Sandbox & AdServices** | `com.android.adservices.api`, `federatedcompute` | ~15 МБ | Пакеты Google для поведенческого трекинга и рекламного профилирования. |
| **`com.libremobileos.vncflinger`** | `/system_ext/priv-app/VncFlinger/VncFlinger.apk` | Пассивный | Вшитый удаленный VNC-сервер экрана. |
| **`batterysecret`** | `/vendor/bin/batterysecret` | 5.3 МБ | Проприетарный демон Xiaomi для проверки серийника батареи и Mi Turbo Charge 33W. |
| **`mlipayd@1.1`** | `/vendor/bin/hw/vendor.xiaomi.hardware.mlipay@1.1-service` | 5.5 МБ | Демон Xiaomi Mi Pay для авторизации в китайских сервисах. |

---

## 4. Скрытые баги и потенциал оптимизации: Где кроется максимальный буст?

### А. Циклический флеппинг экрана (60 Гц $\leftrightarrow$ 144 Гц каждые 3.5 секунды)
В logcat обнаружилась странная аномалия:
Каждые 3.5 секунды демон батареи `healthd` опрашивает контроллер питания. Это дергает SystemUI, экран просыпается в режим 144 Гц, а через 250 мс таймер простоя сбрасывает его на 60 Гц!
Каждое переключение заставляет дисплейный процессор Snapdragon 865 вызывать `HWCDisplay::SubmitDisplayConfig` и `dsi_display_set_mode`, вызывая микрозадержки и лишний расход батареи.  
**Решение:** Закрепить частоту командой `settings put system min_refresh_rate 144.0`.

### Б. Тормозной ZRAM с устаревшим LZO
Смотрим текущую конфигурацию подкачки:
```bash
cat /proc/swaps
# /dev/block/zram0 partition 4194300 kB (4 GB)
cat /sys/block/zram0/comp_algorithm
# [lzo] lz4 zstd
cat /proc/sys/vm/swappiness
# 60
```
При наличии 8 ГБ быстрой физической RAM (свободно более 5.3 ГБ) выделено 4 ГБ ZRAM с медленным алгоритмом `lzo` и агрессивным `swappiness = 60`!  
**Оптимизация:** Переключить алгоритм на `lz4` или `zstd`, а `swappiness` снизить до `30`, чтобы процессор не грелся на сжатии страниц впустую.

### В. Компиляция байткода ART/DEX
`com.android.systemui` уже скомпилирован в машинный код (`status=speed`), однако настройки `com.android.settings` и большинство системных компонентов сидят в режиме `status=verify` (интерпретируются на лету).  
**Оптимизация:** Прогон AOT-компиляции:
```bash
cmd package compile -m speed com.android.settings
```

---

### В. Частота экрана: 144 Гц без компромиссов
Дисплейный контроллер Mi 10T поддерживает честные 144 Гц:
```text
DisplayModeController: setDesiredMode 4630946687422888065 {mode={fps=144.00 Hz, modePtr={id=0, vsyncRate=144.00 Hz, peakRefreshRate=144.00 Hz}}}
```
Аппаратный драйвер панели `qcom,mdss_dsi_j3s_37_02_0a_dsc_video` нативно тянет 144 кадра в секунду. В связке с правильной AOT-компиляцией ART интерфейс становится эталонно плавным.

---

## 5. Итоговая шпаргалка аудита

| Направление | Обнаруженная проблема | Риск / Влияние | Рекомендованное действие |
| :--- | :--- | :--- | :--- |
| **IIO us_prox драйвер** | `read_raw` = NULL в `us_prox.0`. Чтение `in_proximity_raw` роняет ядро в Panic (`ESR 0x86000005`). Спам датчика каждые 8с. | **Критический (Kernel Crash)** | Отвязать `us_prox.0` через unbind или добавить проверку NULL в исходниках ядра. |
| **Батарейный спам** | `fg_psy_get_property` не знает свойства 67 и 4 в Android 15. | Засорение dmesg / logcat | Косметический, отфильтровать или обновить PM8150B driver. |
| **Китайский шпион SOTER** | `com.tencent.soter.soterserver` + `vendor.qti.hardware.soter@1.0` висят в фоне. | 105 МБ RAM впустую, фоновые пробуждения | Заморозить: `pm disable-user com.tencent.soter.soterserver`. |
| **Телеметрия LMOStats** | `com.libremobileos.stats` собирает и передает системную метрику. | 66 МБ RAM, сетевой трафик | Заморозить: `pm disable-user com.libremobileos.stats`. |
| **Служба диагностики** | `com.android.devicediagnostics` непрерывно мониторит ошибки. | 63 МБ RAM | Заморозить: `pm disable-user com.android.devicediagnostics`. |
| **Сжатие ZRAM** | ZRAM 4 ГБ использует устаревший медленный алгоритм `lzo`. | Лишние циклы CPU, повышенный нагрев | Переключить на `lz4` или `zstd`, снизить swappiness до 30-40. |
| **Компиляция ART/DEX** | Все пакеты в режиме `verify` (байткод интерпретируется на лету). | Микрофризы, повышенный жор батареи | Запустить полную AOT-компиляцию: `cmd package compile -m speed-profile -a`. |

Фиксирую финальный снимок экрана системы после аудита:
![Экран системы Mi 10T после аудита](file:///d:/для%20one%20plus%20nord%20n10/ARTICLES/screenshots/mi10t_audit_screen.png)
