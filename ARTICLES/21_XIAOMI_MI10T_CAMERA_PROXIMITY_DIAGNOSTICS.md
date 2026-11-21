# Записки на коленке: Вскрытие Xiaomi Mi 10T — почему ослепли камеры, отвалился Face Unlock и дико шипит динамик при звонке

> **Пациент на столе:** Xiaomi Mi 10T (`M2007J3SY`, кодовое имя `apollo`, Snapdragon 865 `kona`).  
> **Симптомы от владельца:** Не работает распознавание лица (Face Unlock), наглухо мертвы все камеры, а когда кто-то звонит — из разговорного динамика раздается жуткое шипение и белый шум.  
> **Прошивка на борту:** Свежеустановленный кастом на Android 15 — LibreMobileOS (`lmodroid_apollon-userdebug 15 BP1A.250505.005 11`), поверх вендора MIUI 14 (`V14.0.4.0.SJDMIXM`).

---

## 1. Пациент подключен. Погнали в консоль!

Короче, принесли мне этот Mi 10T со словами: *«Накатили классный свежий кастом на 15-м Андроиде, но телефон будто контузило: камеры не запускаются, лицо не сканирует, а при входящем звонке в ухо орет шипение, словно ненастроенный ламповый телевизор»*.

Первым делом втыкаю кабель, поднимаю `adb` и сразу запрашиваю root:
```powershell
& "C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe" devices -l
# 5fcca09 device product:lmodroid_apollon model:M2007J3SY device:apollo transport_id:1
& "C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe" root
# restarting adbd as root
```
Отлично, сборка `userdebug`, рутовый adbd доступен без танцев с бубном.

Первый скриншот рабочего стола — есть:
![Интерфейс Mi 10T](file:///d:/для%20one%20plus%20nord%20n10/ARTICLES/screenshots/mi10t_launcher.png)

Теперь запускаю штатное приложение камеры (Aperture от LineageOS). На экране — мгновенный ступор и краш. Снимаю логcat и вижу классику:
```text
Camera LENS_FACING_BACK verification failed
java.lang.IllegalArgumentException: No available camera can be found. Cams:0
androidx.camera.core.impl.CameraValidator$CameraIdListIncorrectException: Expected camera missing from device.
```
![Вылет камеры](file:///d:/для%20one%20plus%20nord%20n10/ARTICLES/screenshots/mi10t_camera_aperture_awake.png)

Смотрю глобальное состояние камер через дампы Android:
```bash
dumpsys media.camera
# Number of camera devices: 0
# Camera Provider HAL legacy/0-0 static info: 0 devices
```
Система рапортует ровно **ноль** подключенных камер. Ни основной, ни ширика, ни макро, ни фронталки!

---

## 2. Грабли №1: Почему отвалился «сканер лица»?

Владелец жаловался: *«Не работает датчик сканера лица»*.  
Смотри, какая штука: у Xiaomi Mi 10T физически **нет** отдельного инфракрасного 3D-проектора точек или сканера сетчатки (это не iPhone с FaceID и не Mi 8 Explorer Edition с ToF-структурированным светом).  
В Mi 10T распознавание лица работает чисто софтово — через 2D-поток фронтальной камеры (`Samsung S5K3T2` 20MP).

Лезу в `dumpsys biometric` и смотрю на `FaceProvider`:
```text
Dumping for sensorId: 1, provider: FaceProvider
{"service":"FaceProvider\/defaultHIDL"}
```
А в манифесте службы `com.libremobileos.faceunlock` черным по белому прописано:
```text
android.permission.FOREGROUND_SERVICE_CAMERA: granted=true
```
Логика прозрачна как стекло: раз в системе `Number of camera devices: 0`, фронтальная камера не существует для Android, службе распознавания лиц не к чему подключиться — и фича мгновенно отваливается. «Датчик лица» не сломан, потому что отдельного датчика просто нет в природе.

---

## 3. Грабли №2: Откуда берется дикое шипение в динамике при звонке?

И вот тут начался настоящий детектив. Откуда шипение именно при звонке?  
Я полезла в системный лог и наткнулась на бесконечно спамящую ошибку:
```text
E android.hardware.sensors@1.0-service: ERROR: Fix ultrasound sensor so it does not return error from poll()
```
Каждые 8 секунд! В цикле!

Кто не в курсе: в погоне за тонкими рамками инженеры Xiaomi выкинули из Mi 10T классический оптический датчик приближения (который раньше подносили к уху, и экран гас). Вместо него воткнули виртуальный ультразвуковой сенсор от норвежской компании **Elliptic Labs** (`Inner Beauty`).

Как это устроено:
1. Телефон генерирует неслышимый ультразвук частотой около 96 кГц через верхний разговорный динамик.
2. Верхний микрофон ловит отраженное от щеки или уха эхо.
3. Цифровой сигнальный процессор Hexagon (DSP) в Snapdragon 865 рассчитывает дистанцию.

Лезем в конфигурацию аудио-микшера `/vendor/etc/mixer_paths.xml`:
```xml
<path name="ultrasound-proximity">
    <ctl name="Ultrasound Enable" value="On" />
    <ctl name="Ultrasound Mode" value="725" />
</path>

<path name="ultrasound-proximity-output">
    <ctl name="RX_CDC_DMA_RX_1 SampleRate" value="KHZ_96" />
    <ctl name="RX_CDC_DMA_RX_1 Channels" value="One" />
    <ctl name="RX_MACRO RX2 MUX" value="AIF2_PB" />
    <ctl name="RX INT0_2 MUX" value="RX2" />
</path>
```
И смотрим в dmesg ядра:
```text
[ 708.168009] [MIUS] Via ULTRASOUND_TX_PORT_ID enable=1
[ 708.173161] [MIUS] : (mius_ultrasound_tx_port_set) : ultrasound_tx_port: enable=1 ret=0
[ 708.215073] [MIUS] mi ultrasound afe afe cb
```
А теперь кульминация:  
Когда поступает звонок, телефон включает тракт приближения (`ULTRASOUND_TX_PORT_ID`), коммутируя ЦАП разговорного динамика на частоту 96 кГц. Но на этом ядре софтовая обработка Elliptic Labs либо не инициализирована с DSP, либо сорвана. Вместо модулированного ультразвука динамик начинает захлебываться цифровым шумом и высокочастотной грязью, которая просачивается в слышимый диапазон как непрерывное громкое **шипение**.

А когда я попыталась прямо из ядра прочитать состояние датчика через sysfs (`cat /sys/devices/platform/us_prox.0/iio:device3/in_proximity_raw`), ядро тут же схватило панику:
```text
[ 951.370610] Internal error: Oops: 86000005 [#1] PREEMPT SMP
[ 951.370660] pc : (null)
[ 951.370682] lr : iio_read_channel_info+0xa4/0xe8
[ 951.370782] Call trace:
[ 951.370787]            (null)
[ 951.370799]  dev_attr_show+0x20/0x5c
[ 951.370826]  seq_read+0x18c/0x458
[ 951.370832]  kernfs_fop_read+0x54/0x1b4
[ 951.370905] Kernel panic - not syncing: Fatal exception
```
В драйвере `us_prox` этого кастомного ядра функция `read_raw` тупо равна `NULL`! Вызов нулевого указателя `pc : (null)` $\rightarrow$ ребут в ramoops. Ядро буквально сырое.

---

## 4. Докапываемся до сути: Почему на самом деле умерли камеры?

Теперь главное блюдо. Почему же не работают камеры? Железная поломка? Шлейф отошел? Микротрещина в плате?  
Проверяем системные свойства сенсоров Xiaomi:
```bash
getprop | grep persist.vendor.camera.mi.module
# [persist.vendor.camera.mi.module.info]: [back_main=none;back_ultra=none;]
# [persist.vendor.camera.mi.module.infoext]: [front_main=none;back_macro=none;]
```
Все 4 модуля помечены вендором как `none`!

Копаем dmesg с момента старта ядра. И вот он — абсолютный инженерный инсайт:
```text
[ 0.289901] rpmh_regulator_probe: smpf1: could not find RPMh address for resource
[ 0.290041] rpmh_regulator_probe: ldof1: could not find RPMh address for resource
[ 0.290110] rpmh_regulator_probe: ldof2: could not find RPMh address for resource
[ 0.290187] rpmh_regulator_probe: ldof3: could not find RPMh address for resource
[ 0.290264] rpmh_regulator_probe: ldof4: could not find RPMh address for resource
[ 0.290325] rpmh_regulator_probe: ldof5: could not find RPMh address for resource
[ 0.290395] rpmh_regulator_probe: ldof6: could not find RPMh address for resource
[ 0.290460] rpmh_regulator_probe: ldof7: could not find RPMh address for resource
```
А дальше при попытке запустить сенсор:
```text
[ 12.727737] CAM_ERR: CAM-SENSOR: cam_sensor_core_power_up: 1735 cam_vaf get failed -517
[ 12.733115] CAM_ERR: CAM-SENSOR: cam_sensor_core_power_up: 1735 cam_v_custom2 get failed -517
[ 14.272052] CAM_ERR: CAM-CCI: cam_cci_read: 1322 wait_for_completion_timeout rc = -110 FIFO buf_lvl: 0x0
[ 15.776076] CAM_ERR: CAM-CCI: cam_cci_core_cfg: 1779 cam cci err -110 , read, slav 0x34 on dev/master 0/0
[ 15.776080] CAM_WARN: CAM-SENSOR: cam_sensor_match_id: 624 read id: 0x0 expected id 0x682:
[ 15.806374] CAM_ERR: CAM-SENSOR: cam_sensor_core_power_up: 1735 cam_vana get failed -517
```

Смотри, что произошло:
1. В референсных платах Qualcomm Snapdragon 865 питание камер идет через отдельный чип управления питанием **PM8009**, подключенный к шине RPMh под именами `ldof1`..`ldof7`.
2. В Xiaomi Mi 10T китайцы сэкономили/переработали схемотехнику: питание аналоговой части камер (`cam_vana`) и автофокуса (`cam_vaf`) идет через дискретный регулятор `camera_wide_vana_ldo`, запитанный от главного контроллера `pm8150_s5`.
3. Сборщик кастомного ROM (или ядра `4.19.325-cip125-st9-perf`) собрал Device Tree (DTB/DTBO) от референсного Qualcomm или чужой модели (`apollon` / Mi 10T Pro с другими ревизиями), прописав ссылки на `ldof1..ldof7`.
4. Драйвер регуляторов RPMh пытается найти адрес `ldof1` в таблице Command DB, присланной загрузчиком XBL, и закономерно обламывается: `could not find RPMh address for resource`.
5. Регуляторы питания камер **не инициализируются вообще**.
6. При опросе сенсора основной камеры Sony IMX682 (`expected id 0x682`) ядро пытается подать питание (`cam_vaf`, `cam_vana`), получает ошибку `-517` (`-EPROBE_DEFER`), сенсор сидит с 0 Вольт на шине, шина I2C/CCI виснет по таймауту (`rc = -110`), а возвращенный ID сенсора равен `0x0`.
7. Камерный демон видит облом на сенсоре 0 и маркирует весь камерный блок как отсутствующий.

---

## 5. Итог и план лечения

Железо телефона **полностью живо**! Матрицы целы, динамик цел, плата не залита.  
Все три проблемы вызваны кривой сборкой софта и дерева устройств:

| Проблема | Что происходит в системе | Первопричина | Что делать |
| :--- | :--- | :--- | :--- |
| **Не работают камеры** | Сенсоры обесточены (`cam_vana get failed -517`), таймаут I2C `0x34` | DTB/ядро ищет несуществующий PMIC PM8009 (`ldof1-7`), вместо дискретного LDO `camera_wide_vana_ldo` | Прошить правильное ядро / DTBO для `apollo` либо вернуться на проверенный вендор / родной boot.img |
| **Не работает Face Unlock** | Сервис не видит ни одной камеры | Отсутствует отдельный ИК-сканер; распознавание завязано на фронталку | Оживет автоматически, как только ядро подаст питание на камеры |
| **Шипение в динамике при звонке** | Динамик переключается в режим ультразвука 96 кГц (`ULTRASOUND_TX_PORT_ID`) без фильтрации | Драйвер `us_prox` (Elliptic Labs) криво собран в ядре, падает при опросе и шлет мусор в аудио-тракт | Исправить драйвер в ядре (заглушка/реализация `read_raw`) либо отключить ультразвуковой тракт в `mixer_paths.xml` |
