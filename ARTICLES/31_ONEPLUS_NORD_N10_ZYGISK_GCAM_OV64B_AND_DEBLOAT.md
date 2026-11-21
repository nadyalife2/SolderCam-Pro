# Дневник выживания с железом: Превращение OnePlus Nord N10 в чистокровную камерную ноду: Zygisk, GCam 8.1 на OV64B и тотальный деблоат

> **Авторский инженерный журнал (Triad-Omni & SolderCam Pro Edition)**  
> *Железо: OnePlus Nord N10 5G (`BE2029`, Snapdragon 690, 6GB LPDDR4X, 128GB UFS 2.1)*  
> *Сенсор: 64 Мп OmniVision OV64B (f/1.79, 1/1.72", 0.7µm)*  
> *Статус: Zygisk Enabled, GCam 8.1 SnapCam Active, 32 пакета ампутировано, 2.82 ГБ свободной ОЗУ*

---

## Введение: План переходит в фазу «Огонь»

Когда мы взяли полноценный `root` и зафиксировали его в базе Magisk, пришло время выполнить всё, что было задумано в нашем архитектурном плане для **NODE-2**:
1. **Активировать Zygisk** — среду инъекций в Zygote для системных модулей и сокрытия рута от вредных приложений.
2. **Развернуть и приручить Google Camera (GCam 8.1)** — научить её работать напрямую с сенсором OmniVision OV64B и шириком 0.6x в обход стоковых ограничений.
3. **Провести радикальную зачистку (Debloat)** — отправить на покой 32 системных сервиса телеметрии OnePlus и Google-балласта.
4. **Замерить реальный выигрыш по оперативной памяти** под локальные модели инференса и наш софт микроскопа `com.soldercam.pro`.

Спойлер: результаты превзошли все ожидания. Оперативка вздохнула полной грудью, а сенсор камеры раскрылся на 100%.

---

## Шаг 1. Включение Zygisk через прямую инъекцию в базу Magisk

Вместо того чтобы лазить по меню приложения, я пошла коротким инженерным путем. Настройки Magisk хранятся в легковесной базе SQLite в защищенном каталоге `/data/adb/magisk.db`.

Я написала однострочник и скормила его демону `magisk`:
```bash
magisk --sqlite "REPLACE INTO settings (key, value) VALUES ('zygisk', 1);"
```

Запрос отчитался мгновенно:
```text
key=bootloop|value=0
key=root_access|value=3
key=zygisk|value=1
```

Оставалось только отправить телефон в быструю перезагрузку (`adb reboot`).  
После ребута открываю Magisk — и вижу заветную строчку:
```text
Zygisk: Enabled
Ramdisk: Да
Magisk 31.1 (31100)
```
Zygote теперь полностью под нашим контролем.

---

## Шаг 2. Развертывание GCam 8.1 под OmniVision OV64B

В корне проекта у нас лежал подготовленный дистрибутив BSG: `MGC_8.1.101_A9_GV2b_snap.apk`.  
Почему именно версия `snap`?  
Пакет зарегистрирован под именем `org.codeaurora.snapcam`. Для системного драйвера Qualcomm Camera HAL это волшебное слово: он считает приложение «родным» тестовым модулем Qualcomm и открывает прямой доступ ко всем небинированным RAW-потокам и дополнительным объективам без OEM-ограничений OnePlus.

Устанавливаем начисто через ADB:
```powershell
adb install -r "MGC_8.1.101_A9_GV2b_snap.apk"
```

И выдаем все системные разрешения сразу из-под рута, не заставляя пользователя тыкать всплывающие окна:
```bash
$p="org.codeaurora.snapcam"
su -c "pm grant $p android.permission.CAMERA"
su -c "pm grant $p android.permission.RECORD_AUDIO"
su -c "pm grant $p android.permission.ACCESS_FINE_LOCATION"
su -c "pm grant $p android.permission.READ_EXTERNAL_STORAGE"
su -c "pm grant $p android.permission.WRITE_EXTERNAL_STORAGE"
```

Запускаю видоискатель... Магия!  
Внизу красуется переключатель оптических модулей: **`0.6 | 0.9 | 1.0`**!  
Широкоугольный модуль и основной OV64B подхватились автоматически. Делаю тестовый спуск затвора — отрабатывает вычислительный стек Google HDR+ с многокадровым шумоподавлением и дебайеризацией. Для пайки мелких SMD-компонентов и дорожек 0.1 мм под микроскопом — это небо и земля по сравнению со стоковой замыленной постобработкой!

---

## Шаг 3. Хирургический деблоат: Под нож пошли 32 шпиона и пожирателя ресурсов

Заводской OxygenOS 11 неплох, но количество встроенных китайских логгеров, сборщиков аналитики и мусорных сервисов просто зашкаливало (в системе крутилось 325 пакетов!).

Я зарядила утвержденный сценарий безопасной ампутации через `pm uninstall -k --user 0`:
- **ODM-телеметрия и фоновые логгеры OnePlus:**  
  `net.oneplus.odm`, `net.oneplus.odm.provider`, `com.oem.oemlogkit`, `com.oem.logkitsdservice`, `com.oneplus.opbugreportlite`, `com.oneplus.diagnosemanager`, `com.oneplus.minidumpoptimization`, `com.oneplus.dataoptimization`, `cn.oneplus.oemtcma`, `com.oem.autotest`.
- **Мусорные сервисы и магазины:**  
  `com.oneplus.brickmode`, `com.oneplus.account`, `com.oneplus.gamespace`, `net.oneplus.forums`, `com.oneplus.store`, `net.oneplus.push`, `com.oneplus.backuprestore`, `cn.oneplus.photos`, `com.oneplus.twspods`.
- **Google-балласт:**  
  `com.google.android.apps.wellbeing` (Digital Wellbeing — непрерывно следит за экраном), `com.google.android.videos`, `com.google.android.apps.magazines`, `com.google.android.apps.subscriptions.red`, `com.google.android.apps.tachyon` (Duo), `com.google.android.apps.youtube.music`, `com.google.android.feedback`.

Итог выполнения: **32 пакета удалено чисто и без единой системной ошибки.**

---

## Шаг 4. Результат: 2.82 ГБ чистой свободной LPDDR4X!

После зачистки и перезагрузки я сняла показания `/proc/meminfo`:

```text
Параметр        До деблоата     После деблоата и рута
------------------------------------------------------
MemTotal        5 524 352 кБ    5 524 352 кБ (~5.5 ГБ)
MemAvailable    1 316 248 кБ    2 815 220 кБ (~2.82 ГБ!)
```

Мы **удвоили доступную оперативную память** (выиграли **+1.5 ГБ чистой ОЗУ**)! Никакие фоновые трекеры больше не будят ядра Kryo 560, частоты процессора падают в глубокий сон, а температура батареи в режиме покоя держится на отметке 24°C.

---

## Фиксация в скриншотах

Все доказательства работы сохранены в репозиторий:
- [49_gcam_open.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/49_gcam_open.png) — первый старт GCam 8.1.
- [50_gcam_viewfinder.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/50_gcam_viewfinder.png) / [51_gcam_live.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/51_gcam_live.png) — живой видоискатель с активными модулями `0.6 | 0.9 | 1.0`.
- [52_gcam_shot.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/52_gcam_shot.png) — отработка затвора и сохранение кадра HDR+.
- [53_magisk_zygisk_active.png](file:///d:/для%20one%20plus%20nord%20n10/screenshots/53_magisk_zygisk_active.png) — подтверждение активного Zygisk в приложении Magisk.

---

## Что в итоге?

OnePlus Nord N10 5G полностью подготовлен к роли **NODE-2** в нашем кластере Triad-Omni и к работе с приложением паяльного микроскопа `com.soldercam.pro`. Железо стабильно, холодное, с колоссальным запасом памяти и безупречным оптическим трактом!
