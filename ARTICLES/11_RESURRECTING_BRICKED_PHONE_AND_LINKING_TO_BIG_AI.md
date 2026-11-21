# Заметка №11. Воскрешение из ребут-лупа, AST-граф кода с Graphify и превращение древнего Redmi Note 4 в краевой сенсор для Большого ИИ

> **Контекст задачи:** Мы строим распределенный локальный ИИ-кластер, где мощная рабочая станция и Большой ИИ (Antigravity / Gemini) отвечают за тяжелый когнитивный синтез и архитектурную память, а ветеран **Xiaomi Redmi Note 4 (`nikel`, MediaTek Helio X20 MT6797, 3 ГБ ОЗУ, Android 6.0)** берет на себя роль аппаратного пульта (Hardware Deck), краевого зонда телеметрии и ультрабыстрого исполнителя низкоуровневых команд. Но прямо перед стартом телефон внезапно ушел в жесткий циклический ребут.

---

## 1. Входная боль: пациент в коме, ребут каждые 20 секунд

Короче, только я собралась связать Redmi Note 4 с Большим ИИ, как телефон взбесился: экран загорается, показывает рабочий стол на 10 секунд — и аппарат со свистом улетает в перезагрузку. И так по кругу.

Первая мысль любого нормального человека: «Ну всё, флеш-память eMMC 5.1 деградировала от старости». Но я не верю в мистику, пока не увижу системный лог.

Хватаю кабель, ловлю телефон между перезагрузками и вытягиваю краш-дамп через ADB:

```powershell
adb logcat -b crash -d
```

И тут в логах всплывает вот такой «подарочек» от корпорации добра:

```text
FATAL EXCEPTION IN SYSTEM PROCESS: main
Process: system_server, PID: 1354
java.lang.IllegalStateException: Service without Chimera impl: 
  com.google.android.location.geofence.service.GeofenceProviderService
    at com.google.android.chimera.container.AbstractServiceProxy.onCreate()
    at android.app.ActivityThread.handleCreateService(ActivityThread.java:2931)
```

Смотри, какая штука: Google Play Services (`com.google.android.gms`) втихаря обновился до сборки `26.26.34` с `targetSdk=37`. Разработчики Google вычистили из динамического загрузчика Chimera старую реализацию Geofence, посчитав, что на планете уже нет живых устройств на Android 6.0 (Marshmallow). А в коде `services.jar` шестого Андроида системный сервис `GeofenceProxy.java` пытается подключиться к Google-сервису, получает `IllegalStateException` и... роняет весь `system_server`. А падение `system_server` на Android приводит к мгновенной панике ядра и перезагрузке ОС!

---

## 2. Грабли и фейлы: почему «простые» решения не сработали

Попробовала снести сломанное обновление по-быстрому через ADB:
```powershell
adb shell pm uninstall -k --user 0 com.google.android.gms
```

Но консоль выдала издевательское:
```text
Failure [DELETE_FAILED_DEVICE_POLICY_MANAGER]
```

Оказалось, служба «Найти устройство» залочила себя в администраторах устройства (`MdmDeviceAdminReceiver`), а на Android 6.0 утилита `dpm` еще не знала команды принудительного снятия прав.

Перевела телефон в Fastboot:
```powershell
adb reboot bootloader
fastboot devices
# 7LS8SKLV55IZSK7S        fastboot
```

Сделала стандартный `fastboot erase userdata` и `fastboot erase cache`. Перезагружаюсь — и телефон намертво повис на белом логотипе `MI`.

### Почему телефон завис на логотипе MI? (Инженерный инсайт)
Команда `fastboot erase` просто забивает нулями начальные сектора разделов. Она **не создает** суперблок и дерево inode файловой системы ext4. Когда MediaTek-ядро монтирует `/data` при первой загрузке, оно ждет валидную разметку ext4, не находит её и впадает в вечный ступор на этапе инициализации криптографии.

**Лекарство:**
Я распаковала официальную глобальную прошивку `nikel_global_images_V10.2.1.0` и прошила готовые разреженные (sparse) заводские образы с правильной геометрией ext4:

```powershell
fastboot flash userdata userdata.img
fastboot flash cache cache.img
fastboot flash boot boot.img
fastboot reboot
```

За 4 секунды разделы прошились, и Redmi Note 4 чистейше ожил на заводской MIUI 10 с фабричным GMS v10.0.84 в `/system/priv-app/`. Циклический ребут побежден навсегда!

![Воскресший телефон в сети](../screenshots/screen_factory_booted.png)
*Рис. 1. Пациент полностью стабилен: чистый запуск, циклического перезапуска больше нет.*

---

## 3. Картографируем кодовую базу с помощью Graphify

Пока телефон загружался, я решила навести порядок в нашем распределенном репозитории. Проект разросся: микросервисы Melvin, Camera2 API, Bionic-хуки, скрипты Alpine и сетевые шлюзы.

Для интеллектуальной навигации по коду я накатила плагин **Graphify** (`Graphify-Labs/graphify`, пакет `graphifyy`):

```powershell
pip install graphifyy
python -m graphify antigravity install
```

Graphify подтянул 28 грамматик Tree-Sitter (C, C++, Kotlin, Python, Bash, TypeScript) и сгенерировал в нашем проекте правила и скилы для Antigravity:
* `.agents/rules/graphify.md`
* `.agents/workflows/graphify.md`
* `~/.gemini/config/skills/graphify/SKILL.md`

Теперь агент может обходить граф вызовов и архитектурные связи на лету без пожирания контекстного окна.

---

## 4. Превращаем Redmi Note 4 в краевой узел (Edge Node) для Большого ИИ

Мы вернули Termux, подняли SSH-сервер на порту 8022 и запустили изолированный контейнер Alpine Linux 3.20 с Python 3.12.13.

![Терминал готов к работе](../screenshots/screen_termux_ready.png)
*Рис. 2. На телефоне поднят Termux, запущен SSH и Alpine Linux 3.20 (aarch64).*

Теперь самое интересное — архитектура моста.
Большой ИИ (Antigravity на ПК) великолепен в рассуждениях, но он сидит далеко и не может пощупать физическую реальность: нагрев аккумулятора, температуру 10 ядер чипсета, напряжение на контактах. А опрашивать LLM ради простого сложения $125 \times 8 + 45$ — это расточительство токенов и задержка в пару секунд.

Я написала легковесный краевой сервис `xiaomi_edge_node.py` и запустила его в Alpine на порту `5055`.

### Возможности краевого демона:
1. **Прямой опрос контроллеров питания и термодатчиков MediaTek:**
   * Батарейный профиль: `/sys/class/power_supply/battery/capacity`, `batt_temp`, `batt_vol`, `current_now`.
   * Термозоны 10 ядер: `/sys/class/thermal/thermal_zone1/temp` (`mtktscpu`), `mtktspmic`, `mtktsAP`.
2. **Субмиллисекундный локальный роутер (`/api/query`):**
   * Если запрос касается физического состояния устройства («какой заряд батареи?», «температура процессора»), телефон отвечает сам за **< 5 мс**.
   * Если запрошена математика — запускается мгновенный локальный калькулятор.
   * Если запрос требует сложного синтеза или генерации кода — узел прозрачно маркирует его для делегирования Большому ИИ (`big_ai_cluster`).

### Проверка связи: опрос с ПК через REST API
Стучусь с рабочего компьютера в телефон по Wi-Fi:

```powershell
Invoke-RestMethod -Uri "http://192.168.31.48:5055/api/status" -Method Get | ConvertTo-Json
```

**Ответ от живого устройства:**
```json
{
  "node_id": "NODE-3",
  "device_model": "Xiaomi Redmi Note 4 (nikel)",
  "soc": "MediaTek Helio X20 (MT6797) 10-core",
  "role": "Hardware Deck & Edge Probe for Big AI",
  "uptime_seconds": 360958.4,
  "battery": {
    "capacity_percent": 86,
    "temperature_c": 29.0,
    "voltage_v": 4.229,
    "current_ma": -790,
    "status": "Charging",
    "health": "Good"
  },
  "thermal": {
    "mtktscpu": 31.7,
    "mtktspmic": 32.0,
    "mtktsbattery": 29.0
  },
  "ram": {
    "MemTotal_MB": 2717.9,
    "MemAvailable_MB": 1214.1
  }
}
```

Тестирую роутер запросов с кириллицей:
```powershell
$json = [System.Text.Encoding]::UTF8.GetBytes('{"prompt": "какой заряд батареи"}')
Invoke-RestMethod -Uri "http://192.168.31.48:5055/api/query" -Method Post -Body $json -ContentType "application/json; charset=utf-8"
```
**Результат:**
```json
{
  "routed_to": "local_hardware_probe",
  "handled_locally": true,
  "response": "Заряд батареи: 86%, напряжение: 4.231V, температура: 29.0°C, статус: Charging."
}
```

А на сложный вопрос «напиши функцию на Python» телефон мгновенно возвращает:
```json
{
  "routed_to": "big_ai_cluster",
  "handled_locally": false,
  "delegate_reason": "Cognitive reasoning, generative synthesis or code generation required"
}
```

![Активный краевой узел на связи](../screenshots/screen_edge_node_live.png)
*Рис. 3. Краевой демон запущен и интегрирован в кластер: нулевой пинг, прямая телеметрия.*

---

## 5. Итоговая шпаргалка узла и чеклист

| Компонент / Задача | Что было | Что стало | Профит |
| :--- | :--- | :--- | :--- |
| **Google Play Services** | Автообновление v26.26.34 валило `system_server` | Фабричный GmsCore v10.0.84 + блок автоапдейтов | Полная стабильность без ребутов |
| **Файловая система Data** | Пустой затертый раздел после `fastboot erase` | Прошит разреженный `userdata.img` с ext4 inode | Загрузка за 15 секунд |
| **Навигация по коду** | Ручной поиск по файлам | **Graphify AST Knowledge Graph** | Точечный поиск связей без лишних токенов |
| **Связь с Большим ИИ** | Телефон жил сам по себе | REST/JSON-RPC агент на порту `5055` | Двусторонний обмен данными с ПК |
| **Задержка на датчики** | ~2000 мс (запрос в облако/LLM) | **< 5 мс** (локальный sysfs-зонд) | Мгновенный отклик физического пульта |

Старичок Xiaomi Redmi Note 4 официально принят на службу в качестве физического сенсора и пульта управления нашего ИИ-кластера!
