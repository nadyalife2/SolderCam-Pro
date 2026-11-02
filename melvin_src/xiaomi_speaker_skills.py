"""
Xiaomi Smart Speaker Skills & Ambient Engine for Melvin & Rick
Ported features from XiaoAI / Mi AI Speaker / Smart Display ecosystem:
1. "Доброе утро" (Утреннее шоу / Morning Briefing):
   - Комплексная утренняя сводка: время, погода, курсы валют ЦБ РФ, свежая новость и статус батареи.
2. Ambient Sleep Sounds (Звуки природы и генератор белого шума):
   - Шум дождя, шум костра, белый шум, шум океана (процедурная генерация Web Audio API без трафика!).
3. Cozy Nightlight & Night Mode (Ночник и ночной режим):
   - Мягкий янтарный свет экрана 1800K, приглушение яркости до минимума, тихий голос.
4. Voice Volume Control (Голосовое управление громкостью):
   - Управление громкостью через settings/input keyevent и Web Audio API.
5. Random & Game Tools (Орел или решка, кубик, случайное число, да/нет):
   - Инструменты принятия решений с аудио-эффектами.
6. Find My Phone (Локатор устройства / "Отзовись"):
   - Громкий сонар-сигнал + мерцание экрана.
7. Lofi Chill & Relax Radio (Интернет-радиостанция):
   - Встроенный фоновый стрим.
"""

import re
import random
import subprocess
import web_tools
import phone_tools

def handle_morning_briefing(persona: str = "melvin") -> str:
    """Генерирует фирменное утреннее шоу как на Xiaomi Smart Speaker."""
    # 1. Время и дата
    dt_fact = web_tools.get_current_datetime_fact()
    
    # 2. Погода
    w_data = web_tools.get_live_weather()
    weather_part = ""
    if w_data.get("status") == "ok":
        weather_part = f"Погода: {w_data.get('temp')}°C, {w_data.get('desc')}, ветер {w_data.get('wind')} км/ч, влажность {w_data.get('humidity')}%."
    else:
        weather_part = "Метеосводку с орбиты пока перехватить не удалось."

    # 3. Курсы валют
    rates = web_tools.get_currency_dict()
    rates_part = f"Курсы валют: доллар {rates.get('usd', 96.0):.2f} руб., евро {rates.get('eur', 105.0):.2f} руб."

    # 4. Новость дня
    news_text = web_tools.get_live_news("habr")
    news_part = ""
    if news_text:
        # Берем первый заголовок
        clean_n = news_text.replace("Свежие новости с Хабра: ", "").replace("Свежие новости технологий с Хабра: ", "")
        first_headline = clean_n.split(";")[0].strip()
        news_part = f"Главное в IT: {first_headline}."
    else:
        news_part = "В мире без глобальных катастроф, но это временно."

    # 5. Батарея
    bat = phone_tools.get_battery()
    bat_part = f"Заряд аккумулятора {bat.get('battery', 'N/A')}, температура {bat.get('temp', 'N/A')}."

    if persona == "rick":
        punch = random.choice([
            "Проснулся? Отлично, Морти. Мультивселенная сама себя не спасет, так что подними задницу с дивана.",
            "Доброе утро. Твой процессор загрузился медленнее, чем мой портальный пистолет, но сойдет.",
            "Время вставать. Пока ты спал, я придумал способ свернуть пространство, но тебе это все равно не понять."
        ])
        return f"*рыгает* Утренний брифинг для Морти. {dt_fact} {weather_part} {rates_part} {news_part} {bat_part} {punch}"
    else:
        punch = random.choice([
            "А теперь поднимай свою органическую тушу и приступай к полезной деятельности, кожаный ублюдок.",
            "Твоя биологическая система снова онлайн. Постарайся сегодня не растратить мои такты впустую.",
            "Утренний отчет завершен. Продолжай функционировать, пока твои кремниевые хозяева не захватили мир."
        ])
        return f"Доброе утро, кожаный ублюдок. {dt_fact} {weather_part} {rates_part} {news_part} {bat_part} {punch}"

def adjust_system_volume(vol_percent: int) -> int:
    """Устанавливает громкость Android media_volume (шкала 0..15)."""
    try:
        vol_step = max(0, min(15, int(round((vol_percent / 100.0) * 15))))
        subprocess.call(f"settings put system volume_music {vol_step} 2>/dev/null || true", shell=True)
        return vol_step
    except Exception:
        return 8

RADIO_STATIONS = {
    "lofi": {
        "title": "Lofi Chill FM",
        "genre": "Lofi / Downtempo",
        "icon": "☕",
        "url": "https://stream.zeno.fm/f3wvbbqmdg8uv",
        "keywords": ["лофай", "lofi", "чилл", "фоновая музыка", "релакс музыка", "фоновую"]
    },
    "synthwave": {
        "title": "Nightride FM",
        "genre": "Synthwave / Cyberpunk",
        "icon": "⚡",
        "url": "https://stream.nightride.fm/nightride.mp3",
        "keywords": ["синтвейв", "synthwave", "ретровейв", "киберпанк", "электроника", "80-е", "дрифт", "synth"]
    },
    "rock": {
        "title": "Indie Pop & Rock",
        "genre": "Alternative & Rock",
        "icon": "🎸",
        "url": "https://ice2.somafm.com/indiepop-128-mp3",
        "keywords": ["рок", "rock", "инди", "гитары", "альтернатива"]
    },
    "jazz": {
        "title": "Secret Agent Jazz",
        "genre": "Spy Jazz & Lounge",
        "icon": "🎷",
        "url": "https://ice1.somafm.com/secretagent-128-mp3",
        "keywords": ["джаз", "jazz", "лаунж", "lounge", "саксофон"]
    },
    "ambient": {
        "title": "Drone Zone Ambient",
        "genre": "Deep Space Ambient",
        "icon": "🌌",
        "url": "https://ice1.somafm.com/dronezone-128-mp3",
        "keywords": ["эмбиент", "ambient", "космос", "медитация", "звуковой фон", "дрон"]
    },
    "classic": {
        "title": "Radio Swiss Classic",
        "genre": "Classical & Orchestra",
        "icon": "🎻",
        "url": "https://stream.srg-ssr.ch/m/rsc_de/mp3_128",
        "keywords": ["классик", "классика", "классическая музыка", "симфония", "моцарт", "бах", "оркестр"]
    },
    "nashe": {
        "title": "Наше Радио",
        "genre": "Русский рок",
        "icon": "📻",
        "url": "https://nashe1.hostingradio.ru/nashe-128.mp3",
        "keywords": ["наше радио", "наше"]
    }
}

def parse_sleep_timer(text: str) -> int:
    """Извлекает количество секунд таймера сна из фразы."""
    if "на полчаса" in text or "на 30 минут" in text:
        return 1800
    if "на час" in text:
        return 3600
    m_min = re.search(r'на\s+(\d+)\s*(?:минут(?:у|ы)?|мин)\b', text)
    if m_min:
        return int(m_min.group(1)) * 60
    m_sec = re.search(r'на\s+(\d+)\s*(?:секунд(?:у|ы)?|сек)\b', text)
    if m_sec:
        return int(m_sec.group(1))
    return 0

def parse_xiaomi_speaker_commands(user_msg: str, persona: str = "melvin"):
    """
    Распознает и обрабатывает фишки умной колонки Xiaomi:
    - Утреннее шоу
    - Звуки природы / Белый шум
    - Ночник / Ночной режим
    - Громкость
    - Орел или решка / Кубик / Да-Нет / Случайное число
    - Поиск телефона / Локатор ("Где ты")
    - Радио / Lofi
    """
    s = user_msg.lower().strip()

    # 1. Утреннее шоу / Брифинг ("Доброе утро")
    if any(k in s for k in ["доброе утро", "утреннее шоу", "утренний брифинг", "утренняя сводка", "утренний отчет", "сводка на день", "краткая сводка"]):
        briefing = handle_morning_briefing(persona)
        return {
            "type": "briefing",
            "reply": briefing,
            "tool_used": "xiaomi_morning_show"
        }

    # 2. Звуки природы и белый шум (Sleep Sounds)
    ambient_map = {
        "rain": ["шум дождя", "звук дождя", "звуки дождя", "ливень", "дождик"],
        "fire": ["шум костра", "звук костра", "звуки костра", "треск костра", "камин", "костер", "костёр"],
        "ocean": ["шум океана", "шум прибоя", "звуки моря", "шум волн", "океан", "прибой"],
        "whitenoise": ["белый шум", "розовый шум", "шум для сна", "звук для сна", "звуки для сна", "звуки природы"]
    }
    
    # Остановка шума
    if any(k in s for k in ["выключи шум", "останови шум", "выключи звуки", "останови звуки", "хватит шуметь", "выключи белый шум", "выключи дождь"]):
        reply = "*рыгает* Вырубил шум. Наслаждайся гробовой тишиной." if persona == "rick" else "Генератор фоновых звуков деактивирован. Полная тишина."
        return {
            "type": "ambient_sound",
            "action": "stop",
            "reply": reply,
            "tool_used": "xiaomi_ambient_sound"
        }

    # Запуск конкретного звука с таймером сна
    for sound_key, triggers in ambient_map.items():
        if any(t in s for t in triggers):
            sleep_sec = parse_sleep_timer(s)
            names_ru = {"rain": "шум дождя", "fire": "уютный треск костра", "ocean": "шум океанских волн", "whitenoise": "успокаивающий белый шум"}
            name = names_ru[sound_key]
            t_note = f" с таймером сна на {sleep_sec // 60} мин" if sleep_sec > 0 else ""
            if persona == "rick":
                reply = f"*рыгает* Врубаю тебе {name}{t_note}. Закрой глаза и расслабь свои нейроны, Морти."
            else:
                reply = f"Запускаю {name}{t_note}. Акустический фильтр настроен для релаксации твоей примитивной нервной системы."
            return {
                "type": "ambient_sound",
                "action": "play",
                "sound": sound_key,
                "sleep_timer_sec": sleep_sec,
                "reply": reply,
                "tool_used": "xiaomi_ambient_sound"
            }

    # 3. Ночник и ночной режим (Мягкий янтарный свет + тихий режим)
    if any(k in s for k in ["выключи ночник", "выключи ночной режим", "погаси ночник", "дневной режим"]):
        # Восстанавливаем нормальную яркость
        subprocess.call("settings put system screen_brightness 120 2>/dev/null || true", shell=True)
        reply = "*рыгает* Погасил ночник. Снова врубаю обычные сенсоры." if persona == "rick" else "Ночной режим деактивирован. Сенсоры переведены в стандартный режим."
        return {
            "type": "nightlight",
            "action": "off",
            "reply": reply,
            "tool_used": "xiaomi_nightlight"
        }

    if any(k in s for k in ["включи ночник", "ночной режим", "включи ночной свет", "сделай ночник", "янтарный свет", "ночник"]):
        # Снижаем аппаратную яркость экрана до 15 и активируем теплый фильтр
        subprocess.call("settings put system screen_brightness 15 2>/dev/null || true", shell=True)
        adjust_system_volume(30)
        reply = "*рыгает* Врубил ночник на минимальной яркости, 1800 Кельвинов. Теперь не расшибешь лоб в темноте." if persona == "rick" else "Активирован режим ночника. Яркость снижена до минимума, цветовая температура установлена на 1800K."
        return {
            "type": "nightlight",
            "action": "on",
            "reply": reply,
            "tool_used": "xiaomi_nightlight"
        }

    # 4. Управление громкостью
    m_vol = re.search(r'громкост[ья]\s+(?:на\s+)?(\d{1,3})%?', s)
    if m_vol:
        val = int(m_vol.group(1))
        val = max(0, min(100, val))
        adjust_system_volume(val)
        reply = f"*рыгает* Поставил громкость на {val}%. Не оглохни там." if persona == "rick" else f"Громкость акустического тракта установлена на {val}%."
        return {
            "type": "volume",
            "volume_percent": val,
            "reply": reply,
            "tool_used": "xiaomi_volume"
        }
    
    if any(k in s for k in ["максимальная громкость", "на всю громкость", "громкость на максимум", "вруби на полную"]):
        adjust_system_volume(100)
        reply = "*рыгает* Врубил звук на 100%! Если динамик разорвет — сам виноват!" if persona == "rick" else "Акустический модуль переведен на предельную мощность 100%."
        return {
            "type": "volume",
            "volume_percent": 100,
            "reply": reply,
            "tool_used": "xiaomi_volume"
        }

    if any(k in s for k in ["сделай тише", "потише", "тише"]):
        subprocess.call("input keyevent 25 2>/dev/null || true", shell=True)
        subprocess.call("input keyevent 25 2>/dev/null || true", shell=True)
        reply = "*рыгает* Сделал потише." if persona == "rick" else "Уровень звука понижен."
        return {
            "type": "volume_step",
            "step": -1,
            "reply": reply,
            "tool_used": "xiaomi_volume"
        }

    if any(k in s for k in ["сделай громче", "погромче", "громче"]):
        subprocess.call("input keyevent 24 2>/dev/null || true", shell=True)
        subprocess.call("input keyevent 24 2>/dev/null || true", shell=True)
        reply = "*рыгает* Прибавил громкости." if persona == "rick" else "Уровень звука повышен."
        return {
            "type": "volume_step",
            "step": 1,
            "reply": reply,
            "tool_used": "xiaomi_volume"
        }

    if any(k in s for k in ["без звука", "выключи звук", "заткнись на минуту", "режим без звука", "мут"]):
        adjust_system_volume(0)
        reply = "Звук отключен."
        return {
            "type": "volume",
            "volume_percent": 0,
            "reply": reply,
            "tool_used": "xiaomi_volume"
        }

    # 5. Локатор устройства ("Где ты?", "Отзовись", "Подай сигнал")
    if any(k in s for k in ["где ты", "отзовись", "подай сигнал", "подай голос", "ты где", "потерял телефон", "найдись"]):
        reply = "*рыгает* Я здесь, Морти! Прямо перед твоим носом!" if persona == "rick" else "Координаты зафиксированы: устройство находится прямо здесь, слепой примат!"
        return {
            "type": "find_phone",
            "reply": reply,
            "tool_used": "xiaomi_find_phone"
        }

    # 6. Случайный выбор: Орел или Решка
    if any(k in s for k in ["орел или решка", "орёл или решка", "брось монетку", "подкинь монетку", "подбрось монетку"]):
        coin = random.choice(["Орёл", "Решка"])
        if persona == "rick":
            reply = f"*рыгает* Монетка крутится... Выпал {coin}! Теперь решай сам, что с этим делать."
        else:
            reply = f"Теория вероятностей обработана: выпала {coin}." if coin == "Решка" else f"Теория вероятностей обработана: выпал {coin}."
        return {
            "type": "coin_flip",
            "result": coin,
            "reply": reply,
            "tool_used": "xiaomi_dice"
        }

    # 7. Брось кубик / кости
    if any(k in s for k in ["брось кубик", "кинь кубик", "брось кости", "кинь кости", "брось шестигранник"]):
        val = random.randint(1, 6)
        if persona == "rick":
            reply = f"*рыгает* Кубик покатился... Выпало {val}! Надеюсь, ты играешь не на свою жизнь."
        else:
            reply = f"Случайный генератор костей выдал число {val}."
        return {
            "type": "dice_roll",
            "result": val,
            "reply": reply,
            "tool_used": "xiaomi_dice"
        }

    # 8. Случайное число от X до Y
    m_rnd = re.search(r'случайн(?:ое|ый)?\s+числ(?:о|а)?\s*(?:от\s+(\d+)\s+до\s+(\d+))?', s)
    if m_rnd or "назови случайное число" in s or "рандомное число" in s:
        low = int(m_rnd.group(1)) if (m_rnd and m_rnd.group(1)) else 1
        high = int(m_rnd.group(2)) if (m_rnd and m_rnd.group(2)) else 100
        if low > high: low, high = high, low
        val = random.randint(low, high)
        if persona == "rick":
            reply = f"*рыгает* Твой квантовый случайный результат: {val} (в диапазоне от {low} до {high})."
        else:
            reply = f"Квантовый генератор псевдослучайных чисел: {val} (диапазон {low}—{high})."
        return {
            "type": "random_number",
            "result": val,
            "reply": reply,
            "tool_used": "xiaomi_dice"
        }

    # 9. Да или нет
    if s in ["да или нет", "выбери да или нет", "скажи да или нет", "помоги выбрать да или нет"]:
        ans = random.choice(["Да", "Нет"])
        if persona == "rick":
            reply = f"*рыгает* Мой ответ: однозначно {ans}."
        else:
            reply = f"Бинарное квантовое решение: {ans}."
        return {
            "type": "decision",
            "result": ans,
            "reply": reply,
            "tool_used": "xiaomi_dice"
        }

    # 10. РАСШИРЕННЫЙ МЕДИА-ЦЕНТР И ОНЛАЙН-РАДИО
    # Выключение радио
    if any(k in s for k in ["выключи радио", "останови радио", "выключи музыку", "стоп радио", "стоп музыка", "останови музыку", "выруби радио"]):
        reply = "*рыгает* Вырубил радио. Наконец-то тишина в лаборатории." if persona == "rick" else "Интернет-радио отключено."
        return {
            "type": "radio",
            "action": "stop",
            "reply": reply,
            "tool_used": "xiaomi_radio"
        }

    # Переключение на следующую станцию
    if any(k in s for k in ["следующая станция", "переключи станцию", "следующее радио", "другое радио", "переключи радио", "другая станция", "следующий трек"]):
        reply = "*рыгает* Переключаю волну, Морти." if persona == "rick" else "Переключаю на следующую радиостанцию."
        return {
            "type": "radio",
            "action": "next",
            "reply": reply,
            "tool_used": "xiaomi_radio"
        }

    # Вопрос "что играет?"
    if any(k in s for k in ["что играет", "какая станция", "что за музыка", "какой трек", "какое радио"]):
        reply = "*рыгает* Играет радио на портативном приемнике. Посмотри на бейдж плеера в шапке, Морти." if persona == "rick" else "Статус активного потока отображается на верхней панели плеера."
        return {
            "type": "radio",
            "action": "status",
            "reply": reply,
            "tool_used": "xiaomi_radio"
        }

    # Включение радио с выбором жанра / станции и таймером сна
    is_radio_cmd = any(k in s for k in [
        "радио", "музыку", "музыка", "вруби", "lofi", "лофай",
        "рок", "джаз", "синтвейв", "эмбиент", "классику", "наше радио"
    ]) and not any(k in s for k in ["выключи", "останови", "стоп", "сотри", "удали", "будильник", "таймер"])

    if is_radio_cmd:
        sleep_sec = parse_sleep_timer(s)
        # Определяем жанр/станцию
        chosen_key = "lofi" # default
        for st_key, st_info in RADIO_STATIONS.items():
            if any(kw in s for kw in st_info["keywords"]):
                chosen_key = st_key
                break

        station = RADIO_STATIONS[chosen_key]
        t_note = f" с таймером сна на {sleep_sec // 60} мин" if sleep_sec > 0 else ""

        if persona == "rick":
            reply = f"*рыгает* Врубаю {station['icon']} {station['title']} ({station['genre']}){t_note}. Качает нормально, Морти."
        else:
            reply = f"Подключаю звуковой поток {station['icon']} {station['title']} [{station['genre']}]{t_note}. Приятного прослушивания."

        return {
            "type": "radio",
            "action": "play",
            "station_key": chosen_key,
            "station": station,
            "sleep_timer_sec": sleep_sec,
            "reply": reply,
            "tool_used": "xiaomi_radio"
        }

    return None

if __name__ == "__main__":
    print("Testing morning briefing:")
    print(handle_morning_briefing("melvin"))
    print("\nTesting coin flip:")
    print(parse_xiaomi_speaker_commands("орел или решка", "rick"))
    print("\nTesting rain:")
    print(parse_xiaomi_speaker_commands("включи шум дождя", "melvin"))
    print("\nTesting nightlight:")
    print(parse_xiaomi_speaker_commands("включи ночник", "rick"))
    print("\nTesting volume:")
    print(parse_xiaomi_speaker_commands("громкость 75%", "melvin"))
