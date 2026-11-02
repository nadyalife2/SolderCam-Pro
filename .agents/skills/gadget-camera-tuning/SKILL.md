---
name: gadget-camera-tuning
description: Complete engineering guide for smartphone camera tuning, Camera2 API, Qualcomm Snapdragon hardware telemetry, PMIC/BMS diagnostics, NTC thermistor analysis, and Google Camera (GCam) multi-frame HDR+ optimization on mobile gadgets.
---

# Gadget, Camera & Hardware Telemetry Engineering

Экспертное руководство по работе с аппаратной частью мобильных устройств, датчиками камер, низкоуровневой диагностикой питания и алгоритмами обработки изображений.

---

## 1. Архитектура Camera2 API и сенсорный контроль

### Уровни поддержки железа (Hardware Level)
* **Level 3 / FULL**: Полный доступ к сырым RAW10/RAW12 потокам, ручному управлению экспозицией, ISO, фокусным расстоянием и нулевой задержке затвора (ZSL).
* **Сенсор OmniVision OV64B (OnePlus Nord N10 5G / Poco X3 GT / Reno):**
  * Матрица: 1/1.97", 64 Мп Quad Bayer, 0.7μm.
  * Биннинг: 4-in-1 в 16 Мп (4624x3472) для максимальной светочувствительности.
  * Черный уровень (Black Level): `64`, белый уровень (White Level): `1023`.

### Режим «Чистого сенсора» (Bypass ISP Qualcomm)
Для технической съемки (пайка, инспекция микросхем, микроскоп) встроенные шумодавы процессора искажают мелкие дорожки.
Отключение постобработки в `CaptureRequest.Builder`:
```kotlin
// Отключение подавления шума и контурной резкости
builder.set(CaptureRequest.NOISE_REDUCTION_MODE, CaptureRequest.NOISE_REDUCTION_MODE_OFF)
builder.set(CaptureRequest.EDGE_MODE, CaptureRequest.EDGE_MODE_OFF)
builder.set(CaptureRequest.TONEMAP_MODE, CaptureRequest.TONEMAP_MODE_FAST)
```

### Multi-frame RAW Stacking (Многокадровое накопление)
1. Захват пакета из 8–16 кадров `ImageFormat.RAW_SENSOR` в кольцевой буфер `ImageReader`.
2. Попиксельное совмещение с компенсацией микродрожания (Image Alignment).
3. Временное усреднение (Temporal Averaging): снижает шум на $\sqrt{N}$ раз (при 16 кадрах шум падает в 4 раза без потери микрорезкости).
4. Экспорт через `DngCreator` в 16-битный несжатый DNG.

---

## 2. Диагностика питания, PMIC и термодатчиков NTC

### Контроллеры питания
* **Qualcomm PM7250B / TI BQ27541**: Контролируют профили быстрой зарядки (Warp Charge 30W / QC).
* Опасность китайских аккумуляторов-копий: подмена термистора постоянным SMD-резистором $10\,\text{k}\Omega$. Температура застывает на $+24.0^\circ\text{C}$, отключая защиту от перегрева, что при напряжении $4.45\,\text{V}$ приводит к вздутию банки.

### Методика проверки подлинности NTC (NTC Sanity Check)
1. **Программный стресс-тест CPU:** Нагрузка всех 8 ядер процессора на 15–20 секунд.
2. **Анализ кривой:**
   * Настоящий термистор: температура в `thermal_zone` растет на $+2.5 \dots +6.0^\circ\text{C}$.
   * Фальшивый резистор: температура неизменно держится ровно $24.0^\circ\text{C}$ или $25.0^\circ\text{C}$.

### Чтение системных узлов Linux Kernel (через ADB / Root):
```bash
# Напряжение и ток батареи
cat /sys/class/power_supply/battery/voltage_now  # в микровольтах (uV)
cat /sys/class/power_supply/battery/current_now  # в микроамперах (uA)
cat /sys/class/power_supply/battery/temp         # в десятых градуса Цельсия

# Термозоны чипсета и АКБ
cat /sys/class/thermal/thermal_zone*/type
cat /sys/class/thermal/thermal_zone*/temp
```

---

## 3. Настройка и адаптация портов Google Camera (GCam)

### Доступ к вспомогательным модулям без Root
На смартфонах OnePlus с OxygenOS доступ ко 2-й и 3-й камере (широкоугольная, макро) разрешен только для системных имен пакетов:
* `org.codeaurora.snapcam` (рекомендуется)
* `com.android.camera`

### Управление профилями конфигураций (.XML)
* Директория для мода BSG 8.1: `/sdcard/Download/MGC.8.1.101_Configs/`
* Загрузка профиля: двойной клик по темной области возле спуска затвора.

### Оптимизация ночной съемки (Night Sight vs Astrophotography)
* **Астрофотография (Astrophotography)**: делает 15–30 выдержек суммарно на 2–3 минуты. Предназначена **строго для штатива**.
* **Быстрая ночная съемка с рук**: отключение пункта «Астрофотография» в шторке режимов переводит камеру в быстрый HDR+ стекинг за 1–2 секунды с сохранением резкости и стабилизации.

---

## 4. Низкоуровневая диагностика, раскирпичивание (Unbrick) и Fastboot Protocol

### Аппаратная идентификация SoC по шине USB (PnP & VID/PID)
Критически важно отличать платформы до прошивки во избежание перманентного окирпичивания загрузочных секторов:
* **MediaTek (MTK Helio X20 / MT6797, Helio G-серия, Dimensity):**
  * `0E8D:0003` — BROM (Boot ROM режим для SP Flash Tool / mtkclient).
  * `0E8D:2000` — Preloader VCOM порт.
  * `18D1:D00D` / `2717:D00D` — Fastboot режим (`product: nikel`).
* **Qualcomm Snapdragon (SD625 mido, SD690 n10, SD860 vayu):**
  * `05C6:9008` — EDL (Emergency Download Mode / Sahara protocol).
  * `18D1:D00D` — Android Bootloader Interface.

### Архитектура DeviceInterfaceGUID в Google Fastboot
Утилита `fastboot.exe` (AOSP platform-tools) не связывается с произвольными устройствами под управлением `WinUSB.sys`. При вызове Win32 API `SetupDiGetClassDevs` поиск выполняется строго по интерфейсному GUID:
$$\text{DeviceInterfaceGUID} = \{F726BE74-803B-4650-BDE0-FF5619ED320B\}$$
* **Проблема Zadig:** Установка generic WinUSB через Zadig назначает случайный GUID или стандартный USB-класс `{A5DCBF10-6530-11D2-901F-00C04FB951ED}`, из-за чего `fastboot` бесконечно ожидает устройство (`< waiting for any device >`).
* **Решение:** Использование официально подписанного пакета Xiaomi/Google (`android_winusb.inf` + `xiaomiwinusba64.cat`), регистрирующего правильный GUID в `Device Parameters\DeviceInterfaceGUIDs`.

### Безопасные алгоритмы прошивки разделов
* **Режим `clean all` (`flash_all.bat`):** Полная перезапись разделов (`boot`, `recovery`, `system`, `cust`, `lk`, `scp`, `trustzone`, `md1rom`). Не производит блокировку загрузчика.
* **Ловушка `clean all and lock` (`flash_all_lock.bat`):** Категорически запрещена при прошивке устройств с несовпадающим региональным идентификатором (например, Global ROM на China-аппарат) из-за принудительной блокировки OEM и срабатывания аппаратной защиты Xiaomi Anti-Rollback (ARB), приводящей к перманентному бутлупу BROM.
* **Интерпретация логов MiFlash:**
  Сообщение `error:Not catch checkpoint ($fastboot -s .* lock)` при зеленом индикаторе статуса не является сбоем прошивки — это штатное подтверждение того, что загрузчик остался разблокированным в соответствии с конфигурацией `flash_all.bat`.

