# 02. Узел №3: Redmi Note 4 (`192.168.1.203`) — Главный Шлюз, Оркестратор и Веб-Пульт

Шлюз **Triad-Omni Gateway v4.7** — это единый координационный центр кластера. Он объединяет:
1. **Мультипротокольный прокси**: полная совместимость с **Anthropic Messages API (Claude Code)**, **OpenAI Chat Completions API** и **Ollama API**.
2. **Мгновенную смену доменов**: прямое переключение весов LoRA через API `/lora-adapters` на Mi 10T за 5 миллисекунд без перезапуска `llama-server`.
3. **Каскадную эскалацию `/v1/escalate`**:
   - Ошибки по пайке, схемотехнике и коду микроконтроллеров (`solder`, `esp32`, `ui_video`) эскалируются на **DeepSeek Flash API** (`reasoning_effort=60`).
   - Задачи обратной разработки (`reva_android` — бинарники, дампы, реверс прошивок) **никогда не покидают локальную сеть** и эскалируются исключительно на локальный ПК (:8090).
   - Все исправленные пары автоматически сохраняются в датасет `sft_<domain>.jsonl` для последующего дообучения.
4. **Аппаратную надежность**: перенос БД на внутреннюю ext4-память (`~/omni_hub/data/`), потокобезопасность (`ThreadingHTTPServer` + `threading.Lock`), и кэш-дружественный системный промпт.

---

## 1. Подготовка директорий на Redmi Note 4

Выполните в Termux (`ssh -p 8022 192.168.1.203`):

```bash
pkg update -y && pkg install -y python sqlite curl openssh rsync
mkdir -p ~/omni_hub/data/datasets ~/omni_hub/data/backups ~/.termux/boot
chmod 700 ~/omni_hub/data
```

> [!WARNING]
> **Не размещайте базу данных на `/storage/emulated/0` (FUSE/sdcardfs)!**  
> Слой эмуляции FAT/SDCard в Android не поддерживает POSIX-блокировки (`fcntl`/`flock`) и mmap, что приводит к повреждению базы данных SQLite (`database is locked` или повреждение WAL-файла). База должна лежать строго во внутреннем каталоге ext4: `~/omni_hub/data/omni_knowledge.db`.

---

## 2. Запуск шлюза и окружение

Создайте файл `~/omni_env.sh`:
```sh
export OMNI_TOKEN="СМЕНИ_НА_ДЛИННЫЙ_СЛУЧАЙНЫЙ_ТОКЕН"
export DEEPSEEK_API_KEY="sk-..."    # только для эскалации не-приватных доменов
export HUB_URL="http://192.168.1.203:8000"
export MI10T_IP="192.168.1.201"
export NORD_IP="192.168.1.202"
export PC_IP="192.168.1.100"
```

Запуск:
```bash
chmod 600 ~/omni_env.sh
source ~/omni_env.sh
python3 ~/omni_hub/omni_gateway.py
```

Автозапуск при старте смартфона (`~/.termux/boot/start_gateway.sh`):
```bash
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock 2>/dev/null
su -c "echo omni_hub > /sys/power/wake_lock" 2>/dev/null
pgrep sshd >/dev/null || sshd
source "$HOME/omni_env.sh"
pkill -f omni_gateway.py 2>/dev/null; sleep 1
nohup python3 "$HOME/omni_hub/omni_gateway.py" > "$HOME/omni_hub/gateway.log" 2>&1 &
```
```bash
chmod +x ~/.termux/boot/start_gateway.sh
```

---

## 3. Архитектура и ключевые компоненты `omni_gateway.py`

Полный исходный код шлюза находится в репозитории: [`omni_gateway.py`](file:///d:/для%20one%20plus%20nord%20n10/cluster_docs/omni_gateway.py).

### 3.1. Карта LoRA-адаптеров и мгновенное переключение
На главном мозге (Mi 10T) `llama-server` держит в памяти 3 предзагруженных адаптера:
- `id: 0` -> `solder` (пайка, монтаж BGA, микроскопы)
- `id: 1` -> `reva_android` (реверс Android, Smali, ARM64, Chromatix, IDA/Ghidra)
- `id: 2` -> `esp32` (микроконтроллеры, FreeRTOS, PlatformIO, драйверы)

При поступлении запроса шлюз классифицирует тему и отправляет запрос на Mi 10T:
```python
def set_domain_adapter(domain):
    """Мгновенное переключение активного адаптера через POST :8080/lora-adapters."""
    target_id = ADAPTER_MAP.get(domain)
    payload = []
    for d, aid in ADAPTER_MAP.items():
        payload.append({"id": aid, "scale": 1.0 if aid == target_id else 0.0})
    
    # 1. Применяем веса адаптеров
    req = urllib.request.Request(f"{BRAIN_URL}/lora-adapters",
                                data=json.dumps(payload).encode(),
                                headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=3)
    
    # 2. Сбрасываем KV-слот, чтобы не смешивать контекст разных доменов
    req_erase = urllib.request.Request(f"{BRAIN_URL}/slots/0?action=erase", data=b"")
    urllib.request.urlopen(req_erase, timeout=2)
```

### 3.2. Каскад эскалации `/v1/escalate`
Когда локальная модель ошибается (например, ошибка компиляции или верификации кода):
1. Если домен `reva_android` -> запрос отправляется **только** на локальный сервер ПК (`http://192.168.1.100:8090`).
2. Если домен `solder` или `esp32` -> запрос отправляется в облако DeepSeek Flash с параметром `reasoning_effort=60`.
3. Успешный исправленный ответ форматируется в стандарт SFT-пар и дописывается в `~/omni_hub/data/datasets/sft_<domain>.jsonl`.

### 3.3. Поддержка Claude Code и IDE
- **SSE-стриминг** в формате Anthropic Messages API (`event: content_block_delta`, `event: message_stop`).
- Поддержка `ping`-хартбитов каждые 15 секунд для предотвращения таймаутов CLI-агентов.
- Обработка `tools`, `tool_use` и `tool_result`.
- Заглушка токенизатора `/v1/messages/count_tokens` для корректной работы Claude Code без обращения к серверам Anthropic.
- Префиксное кэширование: `system`-промпт держится стабильным и неизменным во всех запросах, а динамический RAG-контекст добавляется в конец пользовательского сообщения.

---

## 4. Сенсорный Киоск-пульт (Dashboard)

Экран Redmi Note 4 работает как аппаратный монитор кластера:
- URL для браузера: `http://192.168.1.203:8000/?kiosk=1`
- Отображает в реальном времени: статус узлов, температуры SoC, свободную память, активный LoRA-домен, накопленные пары датасета и скорость инференса.
- Ручные кнопки быстрого переключения доменов («Пайка», «Реверс», «ESP32», «Авто»).
- Кнопка «Обучить» для запуска подготовки Colab-пакета.
- Режим постоянной подсветки без засыпания:
```bash
su -c "settings put global stay_on_while_plugged_in 7"
```
