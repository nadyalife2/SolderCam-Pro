# Разборка с FOTA-трояном, драйверы Fastboot и тотальная зачистка мусора без рута

> **Автор:** Инженер-практик  
> **Пациент:** Pad 7 Ultra (чип MediaTek MT6737M, 2 GB RAM, 32 GB ROM).  
> **Проблема:** Планшет раскаляется в режиме ожидания, виснет намертво при открытии браузера, свободной оперативной памяти — жалкие 120 МБ.  
> **Цель:** Разблокировать загрузчик, вычистить китайские шпионские модули и разгрузить кремний.

---

## 1. Вскрытие автозагрузки: кто пожирает батарею?

После того как мы выяснили, что под капотом трудится 4-ядерный пенсионер MT6737M с 2 гигабайтами оперативки, встал закономерный вопрос: почему планшет тормозит настолько чудовищно? Даже для 2 ГБ Android Go должен ворочаться сносно.

Я запустила в ADB мониторинг запущенных процессов:

```bash
adb shell top -m 10 -s cpu
```

И в первых же строках увидела знакомого «пассажира»:
```text
com.adups.fota
```

И вот тут начался настоящий цирк. **Adups FOTA** — это печально известный китайский троян-загрузчик, вшитый прямо в системный раздел `/system/priv-app`. Эта штука регулярно просыпается, выходит в сеть в обход любых разрешений, собирает IMEI, геолокацию, список установленных приложений и втихаря скачивает рекламные APK-файлы прямо в фоновый кэш! 

Рядом с ним в оперативной памяти весело резвился целый зоопарк мусора:
* `org.khankids.android` и `org.khanacademy.android`
* `com.catool.crazymoro.attackracing` (игра Crazy Moto, которую никто не ставил)
* `com.stevenjou.popstar` (китайские шарики)
* `com.facebook.katana`, `jp.naver.line.android`, `us.zoom.videomeetings`
* Неудаляемые клоны Google Go, TikTok (`musically`), Maps Go, Navigation Go...

Свободной памяти в системе оставалось **120 МБ**. Процессор постоянно молотил на максимальной частоте 1100 МГц, пытаясь обслужить 40 фоновых служб, а батарея таяла на глазах. Пора доставать скальпель.

---

## 2. Битва с Fastboot: как Windows послала меня лесом

Перед глубокой зачисткой я всегда разблокирую загрузчик (Bootloader Unlock) — это страховка на случай, если система упадет в бутлуп. 

Вбиваю в консоль:
```bash
adb reboot bootloader
```

Планшет послушно гаснет и зависает с крошечной надписью в левом нижнем углу:
```text
=> FASTBOOT mode...
```

Набираю `fastboot devices` — и... тишина. Пустой вывод!

```powershell
PS D:\> fastboot devices
PS D:\> 
```

Спокойно, я этот прикол знаю. Открываю «Диспетчер устройств» Windows и вижу классическую желтую плашку: неизвестное устройство `Android` с восклицательным знаком. 

Смотрим аппаратный ID оборудования:
```text
USB\VID_0E8D&PID_201C
```

`VID 0E8D` — это чистый MediaTek. Но когда планшет переходит в режим Fastboot, он меняет дескриптор USB на `PID 201C`, а Windows 10/11 не имеет встроенного inf-файла для этой комбинации и тупо отключает эндпоинт. 

### Как мы победили драйвер за 60 секунд:
1. Запустила утилиту **Zadig** от имени администратора.
2. В меню выбрала `Options` $\rightarrow$ `List All Devices`.
3. Нашла в выпадающем списке устройство с ID `0E8D 201C` (оно отображалось как `Gadget Serial` или `Android`).
4. Выбрала целевой драйвер: **WinUSB (v6.1.7600.16385)** и нажала заветную кнопку `Replace Driver`.

Windows моргнула списком оборудования, и `fastboot devices` тут же отозвался:
```text
MTK0002504241121130    fastboot
```

---

## 3. Разблокировка загрузчика (Bootloader Unlock)

В современных чипах MediaTek с динамическими разделами и Android 10+ старая команда `fastboot oem unlock` больше не работает. На смену ей пришел стандарт Google:

```bash
fastboot flashing unlock
```

На экране планшета появилось предупреждение мелким шрифтом: *«Нажмите Volume Up для подтверждения сброса и анлока»*. 

Я нажала качельку вверх. Консоль задумалась на **105 секунд** — контроллер eMMC форматировал пользовательский раздел `userdata`, стирая заводские следы и криптографические ключи:

```text
(bootloader) Start to unlock the phone ...
(bootloader) Erasing 'userdata' ...
(bootloader) Erasing 'metadata' ...
OKAY [105.506s]
Finished. Total time: 105.510s
```

Перезагружаем пациента:
```bash
fastboot reboot
```

Планшет включился девственно чистым. На экране приветствия я быстро пропустила настройку Wi-Fi и аккаунтов, повторно активировала режим разработчика и вернулась в терминал.

![Экран планшета после разблокировки](file:///d:/для%20one%20plus%20nord%20n10/screenshots/01_desktop_after_unlock.png)
*Вещдок №4: Первый чистый старт после разблокировки загрузчика.*

---

## 4. Тотальный деблоат через ADB без root-прав

Поскольку рутировать планшет с нестандартным ядром 4.9.188 — это верный способ получить кирпич без заводского бэкапа `boot.img`, мы применили метод изоляции пользователя `pm uninstall --user 0`. 

Пакет физически остается в системном read-only разделе `/system`, но операционная система Android выгружает его из автозагрузки, удаляет все его службы, базы данных и фоновые ресиверы для пользователя 0. Для системы приложение перестает существовать навсегда.

### Черный список пакетов, отправленных под нож:

```bash
# 1. Заводской троян-шпион
adb shell pm uninstall -k --user 0 com.adups.fota

# 2. Левые рекламные игры
adb shell pm uninstall -k --user 0 com.catool.crazymoro.attackracing
adb shell pm uninstall -k --user 0 com.stevenjou.popstar

# 3. Сторонний мусор и соцсети
adb shell pm uninstall -k --user 0 org.khankids.android
adb shell pm uninstall -k --user 0 org.khanacademy.android
adb shell pm uninstall -k --user 0 com.facebook.katana
adb shell pm uninstall -k --user 0 jp.naver.line.android
adb shell pm uninstall -k --user 0 us.zoom.videomeetings
adb shell pm uninstall -k --user 0 com.twitter.android
adb shell pm uninstall -k --user 0 com.zhiliaoapp.musically
adb shell pm uninstall -k --user 0 com.lenovo.anyshare.gps

# 4. Обрезки Google Go и сервисы слежения
adb shell pm uninstall -k --user 0 com.google.android.apps.searchlite
adb shell pm uninstall -k --user 0 com.google.android.apps.tachyon
adb shell pm uninstall -k --user 0 com.google.android.apps.mapslite
adb shell pm uninstall -k --user 0 com.google.android.apps.navlite
adb shell pm uninstall -k --user 0 com.google.android.apps.wellbeing

# 5. Китайские телеметрические тесты
adb shell pm uninstall -k --user 0 com.example.hrftools
adb shell pm uninstall -k --user 0 com.debug.loggerui
adb shell pm uninstall -k --user 0 com.htf.testmode
adb shell pm uninstall -k --user 0 com.mediatek.ygps
adb shell pm uninstall -k --user 0 com.mediatek.lbs.em2.ui
adb shell pm uninstall -k --user 0 com.mediatek.autodialer
```

> **Важный момент:** Хозяин попросил обязательно оставить **WhatsApp** (`com.whatsapp`). Его мы трогать не стали, проверили целостность манифеста и оставили в системе в неприкосновенности.

---

## 5. Добиваем фризы: системный DNS и укрощение анимаций

Чтобы планшет перестал дергаться при открытии окон, я задействовала три секретные настройки низкого уровня Android:

### А. Аппаратное отключение масштабирования анимаций
Графический чип Mali-T720 тратил до 40% времени кадра на отрисовку медленных переходов. Вырубаем их в ноль:
```bash
adb shell settings put global window_animation_scale 0.0
adb shell settings put global transition_animation_scale 0.0
adb shell settings put global animator_duration_scale 0.0
```
Интерфейс стал открываться моментально, без желеобразных рывков.

### Б. Глобальный блокировщик рекламы на уровне сокетов (Private DNS)
Чтобы браузеры и системные компоненты не тянули баннеры и счетчики метрик, мы активировали нативный TLS-резолвер AdGuard прямо в ядре:
```bash
adb shell settings put global private_dns_mode hostname
adb shell settings put global private_dns_specifier dns.adguard-dns.com
```
Теперь ни один рекламный домен даже не сможет отрезолвить IP-адрес — баннеры режутся еще до того, как сетевой пакет долетит до процессора!

> *(Инженерная оговорка: как выяснилось позже при битве за YouTube, многие провайдеры в РФ блокируют порт 853 DoT, вызывая `errno=110` и «Ошибку сети». Если сталкиваетесь с отвалом DNS на домашнем Wi-Fi — отключайте командой `settings put global private_dns_mode off`, о чем подробно рассказано в 4-й части).*


### В. Ограничение фонового жора Google Play Services
Сервисы Google (`com.google.android.gms`) на слабых устройствах с 2 ГБ RAM обожают спонтанно просыпаться и жрать до 200 МБ оперативки. Урезаем им права AppOps:
```bash
adb shell cmd appops set com.google.android.gms RUN_IN_BACKGROUND ignore
adb shell cmd appops set com.google.android.gms RUN_ANY_IN_BACKGROUND ignore
```

---

## 6. Результат: планшет задышал полной грудью

Делаем финальный скриншот рабочего стола:

![Рабочий стол после деблоата](file:///d:/для%20one%20plus%20nord%20n10/screenshots/06_clean_desktop_no_bloat.png)
*Вещдок №5: Идеально чистый рабочий стол без иконок сомнительных китайских игр и троянов.*

Смотрим замеры `free -m`:
* Свободная оперативная память (Free + Available): **выросла с 120 МБ до 350+ МБ**!
* Нагрузка на Swap снизилась почти в три раза.
* Температура корпуса в режиме простоя упала с 43°C до комнатных 31°C.

Планшет очищен от мусора и шпионов, работает стабильно и быстро. Теперь можно превращать его в полноценный мультимедийный центр для кино и YouTube — об этом читайте в третьей части гайда.
