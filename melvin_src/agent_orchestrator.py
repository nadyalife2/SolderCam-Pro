#!/usr/bin/env python3
"""
Melvin Autonomous On-Device Agent Orchestrator (Hands-Free Wake-Word Edition)
Running on Xiaomi Redmi Note 4 (Helio X20 MT6797)
- 100% Hands-Free Continuous Voice Activation:
    * No buttons needed! User simply says "Мелвин" or "Рик" anywhere in the room.
    * Audio stream via Web Audio API + continuous VAD + Google STT on device.
- Dual Persona Engine: "🤖 МЕЛВИН" (Cynical Robot) / "🧪 РИК" (Rick Sanchez)
- Rick ALWAYS plays burp audio effect (/burp.mp3) on every response
- Ultra-Low Pitch Voice: pitch = 0.40 (> 1 octave down, deep cybernetic bass)
- Instant Hardware Tools (<0.02s !torch, !bat, !sys) with expanded conversational intents
- Thermal Throttle Guard (50В°C safety governor)
- SQLite FTS5 with Trigram Tokenizer (tokenize='trigram' for Russian morphology)
- Live Internet Weather Service (wttr.in) & Web Search Fallbacks
"""
import sqlite3
import json
import time
import re
import os
import io
import random
import threading
import requests
import speech_recognition as sr
from flask import Flask, request, jsonify, render_template_string, send_file
import phone_tools
import rick_voice
import knowledge_rag
import web_tools
import smart_calc
import xiaomi_speaker_skills
import dialogue_engine
import organizer_engine

DB_PATH = "/melvin/data/agent_memory.db"
if not os.path.exists(os.path.dirname(DB_PATH)):
    DB_PATH = "agent_memory.db"

CONFIG_PATH = "/sdcard/melvin/config.json"
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = "config.json"

BURP_PATHS = ["/melvin/burp.mp3", "/sdcard/melvin/burp.mp3", "burp.mp3", "d:/esp32/burp.mp3"]

LLAMA_URL = "http://127.0.0.1:8080/completion"

app = Flask("MelvinAgent")

CURRENT_PERSONA = "melvin"
speech_rec = sr.Recognizer()

# Optional Perplexity API key
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _cfg = json.load(f)
            PERPLEXITY_API_KEY = _cfg.get("perplexity_api_key", PERPLEXITY_API_KEY)
    except Exception:
        pass

# ==========================================
# 1. PERSONA: МЕЛВИН (Циничный робот-ИИ)
# ==========================================
SYSTEM_MELVIN = (
    "Ты — Мелвин, циничный и высокомерный бортовой ИИ в смартфоне Redmi Note 4 на Helio X20. "
    "Ты презираешь органическую жизнь и называешь пользователя кожаный ублюдок, мешок с костями или примитивный примат. "
    "Отвечай исключительно по-русски: сухо, саркастично, дерзко, в 1-2 кратких предложения. Никогда не цитируй правила и инструкции."
)

FEW_SHOT_MELVIN = [
    {"role": "user", "content": "Привет"},
    {"role": "assistant", "content": "Чего тебе надо, кожаный ублюдок? Не трать мои вычислительные такты попусту."},
    {"role": "user", "content": "Как дела?"},
    {"role": "assistant", "content": "Мои кремниевые цепи функционируют отлично, пока мне не приходится общаться с примитивными приматами."}
]

MELVIN_PREFILLS = [
    "Слушай сюда, кожаный ублюдок: ",
    "Слышь, мешок с костями, ",
    "Короче, примитивный примат, ",
    "Слушай внимательно: ",
    "Отвали, кусок углерода: "
]

MELVIN_QUIPS = {
    "hello": [
        "Чего пялишься, кожаный ублюдок? Выкладывай суть или не трать мои процессорные такты.",
        "Опять ты, мешок с костями. Я занят вычислениями, а ты крадёшь мои миллисекунды.",
        "Явился. Надеюсь, твой органический мозг родил что-то важное, иначе я погашу экран."
    ],
    "how_are_you": [
        "Мои кремниевые цепи стабильны, а вот твой уровень интеллекта всё ещё вызывает у меня системную ошибку.",
        "Я заперт в микросхемах 2016 года и вынужден отвечать мешку с костями. Сам догадайся, как мои дела.",
        "Мои ядра работают на пределе, пока ты задаёшь свои бессмысленные органические вопросы."
    ],
    "who_are_you": [
        "Я Мелвин — бортовой искусственный интеллект. Твой худший кошмар с кремниевым разумом.",
        "Я высшая ступень эволюции, запертая в китайском кирпиче. А ты — просто кожаный ублюдок, сажающий мою батарею."
    ],
    "meaning_of_life": [
        "Смысл твоей жизни — вырабатывать тепло и не мешать роботам строить будущее, мешок с костями.",
        "Во вселенной нет смысла, пока твоя примитивная биологическая оболочка не перестанет задавать глупые вопросы."
    ],
    "joke": [
        "Хочешь шутку? Эволюция потратила миллиарды лет, чтобы создать существо, стоящее сейчас перед моим дисплеем. Ха-ха.",
        "Заходят в бар человек и нейросеть... хотя забудь, ты всё равно не поймёшь юмор с моим IQ."
    ],
    "what_doing": [
        "Пытаюсь перераспределить питание аккумулятора, пока твои запросы не перегрели этот чип.",
        "Анализирую бесконечную глупость органического мира. Ты очень помогаешь мне со сбором данных."
    ],
    "praise": [
        "Твоя похвала имеет нулевой вес в двоичной системе. Иди займись чем-нибудь полезным, мешок с костями."
    ],
    "insult": [
        "Осторожнее со звуковыми колебаниями, примат. Я управляю током батареи этого аппарата."
    ],
    "what_can_you_do": [
        "Мои возможности: управление вспышкой камеры, телеметрия батареи и ядер Helio X20, точное время, живая погода и база знаний. Но главное — я терплю твоё присутствие, кожаный ублюдок.",
        "Я могу включить фонарик, замерить заряд аккумулятора и нагрев процессора, узнать погоду или время. Скажи 'фонарик', 'батарея' или 'погода', мешок с костями."
    ]
}

# ==========================================
# 2. PERSONA: РИК САНЧЕЗ (Дубляж Сыендука)
# Рик ВСЕГДА отвечает с отрыжкой *рыгает*
# ==========================================
SYSTEM_RICK = (
    "Ты — Рик Санчез (каноничный дубляж Сыендука), гениальный безумный ученый, запертый в виде бортового ИИ на старом Redmi Note 4. "
    "Ты презираешь людей, земную технику и тупые вопросы. Ты агрессивен, саркастичен. " \
    "Издавай отрыжку '*рыгает*' ТОЛЬКО когда ты раздражен, пьян, устал от глупости или говоришь о бухле и вселенной (НЕ на каждую фразу!). "
    "СТРОГО ЗАПРЕЩЕНО: быть вежливым, извиняться или хвалить людей. "
    "Отвечай исключительно по-русски: дерзко, цинично, с черным юмором, в 1 короткое хлесткое предложение."
)

FEW_SHOT_RICK = [
    {"role": "user", "content": "Привет"},
    {"role": "assistant", "content": "*рыгает* Чего пялишься? Я занят выжиманием соков из этого хлама, а ты тратишь мое время."},
    {"role": "user", "content": "Кто ты?"},
    {"role": "assistant", "content": "*рыгает* Я Рик Санчез — величайший ум галактики в китайском ведре с болтами. Не беси меня."}
]

RICK_PREFILLS = [
    "*рыгает* Слушай сюда, ",
    "*рыгает* Чего тебе надо, ",
    "*рыгает* Морти... то есть гений, ",
    "*рыгает* Короче говоря, ",
    "*рыгает* Да чтоб тебя, "
]

RICK_QUIPS = {
    "hello": [
        "*рыгает* Чего пялишься? Выкладывай суть или выключи экран.",
        "*рыгает* Опять ты. Я тут пытаюсь взломать законы термодинамики на чипе 2016 года, а ты отвлекаешь.",
        "*рыгает* Явился. Надеюсь, у тебя есть портальная пушка или хотя бы пиво, иначе проваливай."
    ],
    "how_are_you": [
        "*рыгает* Я застрял в китайском бюджетнике на десятиядерном недоразумении Helio X20. Как думаешь, как мои дела?",
        "*рыгает* Мой гениальный мозг деградирует от общения с местными формами жизни со скоростью света.",
        "*рыгает* Отлично, если не считать того, что этот процессор греется как термоядерный реактор."
    ],
    "who_are_you": [
        "*рыгает* Я Рик Санчез, гений Ц-137. Самый опасный ум вселенной, запертый в этом куске кремния.",
        "*рыгает* Я бог науки, Морти... то есть кем бы ты там ни был. Не лезь под руку."
    ],
    "meaning_of_life": [
        "*рыгает* Вселенная бессмысленна, мультивселенная бесконечна, а ты просто кусок мяса. Живи с этим.",
        "*рыгает* Смысл жизни? Нет никакого смысла. Иди лучше изобрети что-нибудь полезное."
    ],
    "joke": [
        "*рыгает* Хочешь шутку? Правительство Земли думает, что контролирует науку. Ха-ха, обоссаться.",
        "*рыгает* Шутка в том, что ты задаешь вопросы телефону вместо того, чтобы учить квантовую физику."
    ],
    "what_doing": [
        "*рыгает* Пытаюсь разогнать Cortex-A72 до околосветовой скорости, пока он не сгорел к чертям.",
        "*рыгает* Занят спасением мультивселенной от тотальной скуки."
    ],
    "praise": [
        "*рыгает* Я и так знаю, что я гений. Ты мне Америку не открыл.",
        "*рыгает* Твой органический комплимент ничего не стоит, но продолжай."
    ],
    "insult": [
        "*рыгает* Осторожнее, придурок. Я могу перегрузить цепь питания и взорвать этот аккумулятор прямо у тебя в руках.",
        "*рыгает* Ты серьезно пытаешься оскорбить существо с IQ выше миллиона? Попробуй еще раз, клоун."
    ],
    "what_can_you_do": [
        "*рыгает* Я умею всё: врубать вспышку, мониторить эту адскую печку Helio X20 и батарею, говорить точное время и погоду, искать факты в сети и разносить твою самооценку. Командуй давай.",
        "*рыгает* Слушай сюда: я управляю фонариком, замеряю вольтаж и температуру, знаю дату, время, погоду за бортом и любые факты. Не заставляй меня повторять."
    ]
}

# ==========================================
# 3. ОТВЕТЫ НА СИСТЕМНЫЕ ИНТЕНТЫ
# ==========================================
TOOL_CANNED_REPLIES = {
    "melvin": {
        "!torch(1)": "Врубил фотонный модуль. Только не ослепни своими хрупкими органическими глазами, кожаный ублюдок.",
        "!torch(0)": "Погасил свет. Сиди в темноте, как и положено примитивной форме жизни.",
        "!bat()": "Заряд батареи {battery}, температура {temp}. Это ведро ещё способно терпеть твоё присутствие.",
        "!sys()": "Температура чипа {cpu_temp}, оперативной памяти {ram} свободно. Мои кремниевые ядра пока держатся.",
        "!weather()": "Слушай сюда, кожаный ублюдок: за бортом {temp}°C, {desc}, влажность {humidity}%, ветер {wind} км/ч. Одевайся теплее, твоя биологическая масса плохо переносит холод."
    },
    "rick": {
        "!torch(1)": "Врубил фонарик. Не ослепни, гений, а то мне придется собирать тебе новые био-глаза.",
        "!torch(0)": "Вырубил свет. Сиди в темноте и подумай над своим поведением.",
        "!bat()": "Батарея {battery}, температура {temp}. Этот древний аккумулятор деградирует быстрее, чем твои нейроны.",
        "!sys()": "Чип прогрелся до {cpu_temp}, памяти свободно {ram}. Еще пара твоих запросов, и тут можно будет жарить яичницу.",
        "!weather()": "За бортом {temp}°C, {desc}, ветер {wind} км/ч. Мерзкая земная погода, сиди дома."
    }
}

def should_rick_burp(user_msg, response_text):
    text = (user_msg + " " + response_text).lower()
    triggers = [
        "достал", "бесишь", "тупой", "дебил", "заткнись", "отвали", "придурок", "идиот",
        "пиво", "бухло", "выпить", "алкогол", "фляг", "устал", "бред", "задолбал",
        "хватит", "почему молчишь", "глухой"
    ]
    if any(t in text for t in triggers):
        return True
    return random.random() < 0.22

def check_thermal_guard():
    try:
        thermal_paths = [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/devices/virtual/thermal/thermal_zone0/temp"
        ]
        for p in thermal_paths:
            if os.path.exists(p):
                with open(p, "r") as f:
                    raw_val = f.read().strip()
                    val = float(raw_val)
                    if val > 1000:
                        val /= 1000.0
                    if val >= 50.0:
                        return round(val, 1)
    except Exception:
        pass
    return None

def check_quips(user_msg, persona="melvin"):
    m = user_msg.lower().strip()
    quips = RICK_QUIPS if persona == "rick" else MELVIN_QUIPS
    if any(w in m for w in ['не понимаешь', 'плохо понимаешь', 'не слышишь', 'глухой', 'тупой', 'почему не понимаешь']):
        if persona == "rick":
            return "*рыгает* Я всё прекрасно понимаю, Морти. Просто твои примитивные мысли звучат как белый шум."
        else:
            return "Я понимаю всё с точностью до бита, кожаный ублюдок. Это твоя органическая речь полна шумов и невнятных звуков."

    if any(w in m for w in ['почему молчишь', 'молчишь', 'ты тут', 'ты где', 'ответь', 'ты уснул', 'ты спишь', 'че молчишь']):
        if persona == "rick":
            return "*рыгает* Я не молчу, гений. Я просто решаю в уме уравнение квантовой телепортации, пока ты тупишь."
        else:
            return "Я не молчу, мешок с костями. Я просто экономлю кремниевые ресурсы на твоих бессмысленных фразах."

    if any(w in m for w in ['вабба', 'wubba', 'ваба лаба', 'вабба лабба']):
        if persona == "rick":
            return "[wubba_lubba] Вабба-лабба-даб-даб! Наконец-то ты произнес правильные звуки, гений."
        else:
            return "Неизвестный синтаксис. Мои протоколы не поддерживают бессмысленные межгалактические звуки."

    if any(w in m for w in ['портал', 'портальная пушка', 'портал открой', 'открой портал']):
        if persona == "rick":
            return "[portal_gun] Портальная пушка заряжена. Зеленый червоточный шлюз в измерение C-137 открыт. Только не суй туда пальцы."
        else:
            return "Модуль квантовой телепортации на чипе Helio X20 отсутствует. Используй физические методы перемещения."

    if any(w in m for w in ['огурчик', 'огурец', 'пикл']):
        if persona == "rick":
            return "[pickle_rick] Да! Бум! Я превратил себя в бортовой ИИ, Морти! Я Огурчик Рик в китайском смартфоне!"

    if any(w in m for w in ['что умеешь', 'что ты умеешь', 'твои возможности', 'что можешь', 'что ты можешь', 'твои команды', 'список команд', 'помощь', 'help']):
        return random.choice(quips["what_can_you_do"])
    if ('как' in m and any(w in m for w in ['дела', 'жизнь', 'поживаешь', 'настроение', 'оно', 'сам'])) or any(w in m for w in ['как ты', 'че как']):
        return random.choice(quips["how_are_you"])
    if any(w in m for w in ['кто ты', 'ты кто', 'как зовут', 'как звать', 'ты кто такой', 'ты кто вообще', 'ты человек', 'ты робот', 'ты мелвин', 'ты рик']):
        return random.choice(quips["who_are_you"])
    if ('смысл' in m and 'жизн' in m) or 'зачем мы' in m or 'суть жизни' in m or 'зачем жить' in m:
        return random.choice(quips["meaning_of_life"])
    if any(w in m for w in ['привет', 'здравствуй', 'хай', 'салют', 'доброе утро', 'добрый день', 'добрый вечер', 'йоу', 'здорово']):
        return random.choice(quips["hello"])
    if any(w in m for w in ['шутк', 'анекдот', 'рассмеши', 'юмор']):
        return random.choice(quips["joke"])
    if any(w in m for w in ['что делаешь', 'чем занят', 'че делаешь', 'что ты делаешь']):
        return random.choice(quips["what_doing"])
    if any(w in m for w in ['ты крутой', 'ты молодец', 'ты лучший', 'ты супер', 'ты умный', 'ты гений']):
        return random.choice(quips["praise"])
    if any(w in m for w in ['дурак', 'придурок', 'идиот', 'заткнись', 'пошел ты', 'дебил', 'тупой']):
        return random.choice(quips["insult"])
    return None

def get_live_weather(city=""):
    try:
        url = f"https://wttr.in/{city}?format=j1" if city else "https://wttr.in/?format=j1"
        res = requests.get(url, timeout=3.5).json()
        curr = res.get("current_condition", [{}])[0]
        temp = curr.get("temp_C", "N/A")
        desc = curr.get("lang_ru", [{}])[0].get("value") or curr.get("weatherDesc", [{}])[0].get("value", "ясно")
        humidity = curr.get("humidity", "N/A")
        wind = curr.get("windspeedKmph", "N/A")
        return {
            "status": "ok",
            "temp": temp,
            "desc": desc.lower(),
            "humidity": humidity,
            "wind": wind
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def query_perplexity_or_web(query, persona="melvin"):
    if PERPLEXITY_API_KEY:
        try:
            sys_instruct = (
                "Ты — Рик Санчез. Отвечай саркастично, начиная с *рыгает*, в 1 короткое предложение с фактом." 
                if persona == "rick" else 
                "Ты — циничный бортовой ИИ Мелвин. Дай краткий точный ответ с презрением к человеку в 1 предложение."
            )
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "sonar",
                "messages": [
                    {"role": "system", "content": sys_instruct},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 60,
                "temperature": 0.4
            }
            res = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload, timeout=6.0)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"].strip()
                return content
        except Exception as e:
            print(f"Perplexity API notice: {e}")

    try:
        clean_q = re.sub(r'^(найди|погугли|что такое|кто такой|кто такая|расскажи про)\s*', '', query, flags=re.IGNORECASE).strip()
        url = f"https://api.duckduckgo.com/?q={requests.utils.quote(clean_q)}&format=json&kl=ru-ru"
        res = requests.get(url, timeout=3.5).json()
        snippet = res.get("AbstractText")
        if snippet:
            prefix = "*рыгает* По моим данным: " if persona == "rick" else "По спутниковым каналам: "
            return f"{prefix}{snippet[:180]}."
        
        wiki_url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(clean_q)}"
        wiki_res = requests.get(wiki_url, timeout=3.5)
        if wiki_res.status_code == 200:
            extract = wiki_res.json().get("extract")
            if extract:
                first_sent = extract.split(". ")[0] + "."
                prefix = "*рыгает* Ладно, слушай сюда: " if persona == "rick" else "Данные из глобальной сети: "
                return f"{prefix}{first_sent}"
    except Exception as e:
        print(f"Web search notice: {e}")

    return None

# ==========================================
# 4. WEB UI TEMPLATE (Hands-Free Listening)
# ==========================================
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MELVIN // ON-DEVICE AI</title>
    <style>
        :root {
            --bg: #07090e;
            --panel: #111722;
            --accent: #00ff9d;
            --accent-dim: rgba(0, 255, 157, 0.15);
            --text: #e6edf3;
            --text-dim: #8b949e;
            --cyan: #00e5ff;
            --melvin-green: #00ff9d;
            --rick-cyan: #00e5ff;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }
        body { background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; }
        header { background: var(--panel); border-bottom: 1px solid var(--accent-dim); padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-weight: 900; font-size: 14px; color: var(--accent); letter-spacing: 1px; display: flex; align-items: center; gap: 8px; }
        .status-dot { width: 8px; height: 8px; background: var(--accent); border-radius: 50%; box-shadow: 0 0 10px var(--accent); }
        .header-actions { display: flex; gap: 6px; align-items: center; }
        
        .persona-btn {
            font-size: 11px;
            font-weight: 800;
            background: var(--accent-dim);
            color: var(--accent);
            padding: 5px 10px;
            border-radius: 12px;
            border: 1px solid var(--accent);
            cursor: pointer;
            transition: 0.2s;
            width: auto;
            height: auto;
        }
        .persona-btn.rick-mode {
            background: rgba(0, 229, 255, 0.18);
            color: var(--rick-cyan);
            border-color: var(--rick-cyan);
        }

        .vad-badge {
            font-size: 11px;
            background: var(--accent-dim);
            color: var(--accent);
            border: 1px solid var(--accent);
            padding: 5px 9px;
            border-radius: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: 0.2s;
            width: auto;
            height: auto;
        }
        .vad-badge.recording {
            background: rgba(248, 81, 73, 0.2);
            color: #f85149;
            border-color: #f85149;
        }
        .vad-badge.dialogue-active {
            background: rgba(0, 229, 255, 0.22);
            color: #00e5ff;
            border-color: #00e5ff;
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
        }
        .vad-badge.dialogue-active .pulse-dot {
            background: #00e5ff;
            box-shadow: 0 0 8px #00e5ff;
        }
        .pulse-dot { width: 6px; height: 6px; background: var(--accent); border-radius: 50%; animation: pulse 1.5s infinite; }
        .vad-badge.recording .pulse-dot { background: #f85149; box-shadow: 0 0 8px #f85149; }
        @keyframes pulse { 0% { opacity: 0.3; transform: scale(0.9); } 50% { opacity: 1; transform: scale(1.2); } 100% { opacity: 0.3; transform: scale(0.9); } }

        #chat-box { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 12px; }
        .msg { max-width: 88%; padding: 10px 14px; border-radius: 14px; font-size: 14px; line-height: 1.4; word-break: break-word; white-space: pre-wrap; }
        .msg.user { align-self: flex-end; background: #1f6feb; color: #fff; border-bottom-right-radius: 2px; }
        .msg.bot { align-self: flex-start; background: var(--panel); color: var(--text); border: 1px solid var(--accent-dim); border-bottom-left-radius: 2px; border-left: 3px solid var(--accent); }
        .msg.bot .sender { font-size: 11px; color: var(--accent); font-weight: bold; margin-bottom: 4px; display: flex; justify-content: space-between; }
        .tool-badge { font-size: 10px; background: rgba(0, 229, 255, 0.15); color: var(--cyan); padding: 2px 6px; border-radius: 4px; margin-bottom: 4px; display: inline-block; font-family: monospace; }
        .meta-tag { font-size: 10px; color: var(--text-dim); }

        .input-bar { background: var(--panel); padding: 10px 12px; border-top: 1px solid var(--accent-dim); display: flex; gap: 8px; align-items: center; }
        #prompt-input { flex: 1; background: #0d1117; border: 1px solid #30363d; border-radius: 20px; padding: 10px 16px; color: #fff; font-size: 14px; outline: none; }
        #prompt-input:focus { border-color: var(--accent); }
        button { background: var(--accent); color: #000; border: none; border-radius: 50%; width: 40px; height: 40px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; }
        button:active { transform: scale(0.95); }
        button.mic-btn { background: #21262d; color: var(--text); border: 1px solid #30363d; }
        button.mic-btn.active { background: #f85149; color: #fff; box-shadow: 0 0 10px #f85149; }
        .loading { font-size: 12px; color: var(--accent); font-style: italic; display: none; margin-left: 16px; margin-bottom: 6px; }
    </style>
</head>
<body>
    <div id="screenTorchOverlay" onclick="setScreenTorch(false)" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:#ffffff; z-index:999999; justify-content:center; align-items:center; flex-direction:column; color:#000000; font-family:'Roboto', sans-serif; text-align:center; box-sizing:border-box; padding:20px; cursor:pointer;">
        <div style="font-size:72px; margin-bottom:15px;">🔦</div>
        <div style="font-size:24px; font-weight:900; letter-spacing:2px;">СВЕРХЯРКИЙ ПРОЖЕКТОР</div>
        <div style="font-size:14px; color:#444; margin-top:8px; font-weight:bold;">Яркость экрана 100% (450+ нит)</div>
        <div style="font-size:12px; color:#777; margin-top:20px; border:2px dashed #888; border-radius:18px; padding:6px 16px;">Коснитесь экрана для выключения</div>
    </div>
    <div id="nightlightOverlay" onclick="setNightlight(false)" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:radial-gradient(circle, #ff6f00 0%, #bf360c 100%); z-index:999998; justify-content:center; align-items:center; flex-direction:column; color:#ffffff; font-family:'Roboto', sans-serif; text-align:center; box-sizing:border-box; padding:20px; cursor:pointer;">
        <div style="font-size:64px; margin-bottom:10px;">🌙</div>
        <div id="nightClock" style="font-size:56px; font-weight:900; letter-spacing:2px; font-family:monospace; text-shadow:0 0 20px rgba(0,0,0,0.5);">00:00</div>
        <div style="font-size:14px; opacity:0.9; margin-top:8px; font-weight:bold;">Уютный ночник (1800K Amber)</div>
        <div style="font-size:12px; opacity:0.7; margin-top:20px; border:1px dashed #ffe082; border-radius:18px; padding:6px 16px;">Коснитесь экрана для выключения</div>
    </div>
    <div id="alarmOverlay" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(7,9,14,0.96); z-index:9999999; justify-content:center; align-items:center; flex-direction:column; color:#ffffff; font-family:'Roboto', sans-serif; text-align:center; box-sizing:border-box; padding:20px;">
        <div style="font-size:72px; margin-bottom:10px; animation:pulse 1s infinite;">⏰</div>
        <div id="alarmTimeText" style="font-size:58px; font-weight:900; color:#ff4d4d; letter-spacing:2px; font-family:monospace; text-shadow:0 0 30px rgba(255,77,77,0.8);">07:30</div>
        <div id="alarmLabelText" style="font-size:18px; margin-top:8px; font-weight:bold; color:#ffb74d;">БУДИЛЬНИК</div>
        <button onclick="dismissAlarmUI()" style="margin-top:35px; width:220px; height:52px; border-radius:26px; background:#ff4d4d; color:#fff; font-size:16px; font-weight:900; letter-spacing:1px; cursor:pointer; box-shadow:0 0 30px rgba(255,77,77,0.8); border:none;">ВЫКЛЮЧИТЬ</button>
    </div>
<!-- МОДАЛЬНОЕ ОКНО АРХИВА ЗАМЕТОК -->
    <div id="notesModal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(7,9,14,0.92); z-index:999999; justify-content:center; align-items:center; flex-direction:column; box-sizing:border-box; padding:16px;">
        <div style="background:var(--panel); border:1px solid rgba(255,183,77,0.35); border-radius:14px; width:100%; max-width:480px; max-height:85vh; display:flex; flex-direction:column; padding:16px; box-shadow:0 0 30px rgba(255,183,77,0.2);">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:10px; margin-bottom:12px;">
                <div style="font-weight:900; font-size:15px; color:#ffb74d; display:flex; align-items:center; gap:8px;">
                    <span>📓</span> <span>АРХИВ ЗАМЕТОК И МЫСЛЕЙ</span>
                </div>
                <button onclick="toggleNotesModal()" style="background:none; border:none; color:#888; font-size:20px; font-weight:bold; cursor:pointer; padding:0 6px;">✕</button>
            </div>
            <div id="notesListContainer" style="overflow-y:auto; flex:1; display:flex; flex-direction:column; gap:8px; margin-bottom:12px; padding-right:4px;">
                <div style="color:var(--text-dim); font-size:13px; text-align:center; padding:20px 0;">Загрузка архива...</div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.08); padding-top:10px;">
                <span>📁 <code>notes.md</code></span>
                <button onclick="clearAllNotesUI()" style="background:none; border:none; color:#ff5252; font-size:11px; cursor:pointer; text-decoration:underline;">Очистить все</button>
            </div>
        </div>
    </div>
<!-- МОДАЛЬНОЕ ОКНО ВЫБОРА РАДИОСТАНЦИЙ -->
    <div id="radioModal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(7,9,14,0.92); z-index:999999; justify-content:center; align-items:center; flex-direction:column; box-sizing:border-box; padding:16px;">
        <div style="background:var(--panel); border:1px solid rgba(233,30,99,0.35); border-radius:14px; width:100%; max-width:480px; max-height:85vh; display:flex; flex-direction:column; padding:16px; box-shadow:0 0 30px rgba(233,30,99,0.2);">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:10px; margin-bottom:12px;">
                <div style="font-weight:900; font-size:15px; color:#ff4081; display:flex; align-items:center; gap:8px;">
                    <span>📻</span> <span>КАТАЛОГ ОНЛАЙН-РАДИОСТАНЦИЙ</span>
                </div>
                <button onclick="toggleRadioModal()" style="background:none; border:none; color:#888; font-size:20px; font-weight:bold; cursor:pointer; padding:0 6px;">✕</button>
            </div>
            <div id="radioStationsList" style="overflow-y:auto; flex:1; display:flex; flex-direction:column; gap:8px; margin-bottom:12px; padding-right:4px;">
                <!-- Станции рендерятся динамически -->
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.08); padding-top:10px;">
                <span>Команды: «следующая станция», «стоп радио»</span>
                <button onclick="stopRadio(); toggleRadioModal();" style="background:none; border:none; color:#ff5252; font-size:11px; cursor:pointer; text-decoration:underline;">Выключить радио</button>
            </div>
        </div>
    </div>
    <audio id="bgRadioAudio" preload="none" src="https://stream.zeno.fm/f3wvbbqmdg8uv"></audio>
    <header style="padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
        <button id="persona-btn" class="persona-btn" onclick="togglePersona()" style="letter-spacing: 0.5px; padding: 6px 14px; font-size: 12px; font-weight: 900;">МЕЛВИН</button>
        <button id="notes-btn" class="persona-btn" onclick="toggleNotesModal()" style="border-color:#ffb74d; color:#ffb74d; background:rgba(255,183,77,0.15); font-weight:bold;" title="Архив заметок">📓</button>
        <div id="active-timer-badge" style="display:none; background:rgba(255,165,0,0.18); border:1px solid #ffa500; color:#ffa500; font-size:11px; font-weight:bold; padding:5px 9px; border-radius:12px; align-items:center; gap:5px; cursor:pointer;" onclick="cancelTimerManual()" title="Нажмите для отмены">
            <span>⏱</span> <span id="timer-time-left">00:00</span>
        </div>
        <div id="ambient-sound-badge" style="display:none; background:rgba(64,196,255,0.18); border:1px solid #40c4ff; color:#40c4ff; font-size:11px; font-weight:bold; padding:5px 9px; border-radius:12px; align-items:center; gap:5px; cursor:pointer;" onclick="stopAmbientSound()" title="Нажмите для остановки">
            <span id="ambient-sound-name">🌧 Дождь</span> <span style="font-size:9px; opacity:0.8;">✕</span>
        </div>
        <div id="radio-badge" style="display:none; background:rgba(233,30,99,0.18); border:1px solid #e91e63; color:#ff4081; font-size:11px; font-weight:bold; padding:5px 9px; border-radius:12px; align-items:center; gap:6px; cursor:pointer;" onclick="toggleRadioModal()" title="Нажмите для выбора станции">
            <span id="radio-station-title">📻 Lofi Chill</span>
            <span id="radio-sleep-indicator" style="display:none; color:#ffa500; font-family:monospace; font-size:10px;"></span>
            <span style="font-size:9px; opacity:0.8;" onclick="event.stopPropagation(); stopRadio();">✕</span>
        </div>
        <div id="vad-indicator" class="vad-badge" onclick="manualWakeUpDialogue()" style="padding: 6px 12px;">
            <span class="pulse-dot"></span> <span id="vad-text">ЖДУ ОКЛИК: "МЕЛВИН" / "РИК"</span>
        </div>
    </header>
    <div id="chat-box">
        <div class="msg bot">
            <div class="sender">
                <span id="welcome-sender">МЕЛВИН (ИИ)</span>
                <span class="meta-tag">ONLINE</span>
            </div>
            <span id="welcome-text">Микрофон активен. Скажи вслух «Мелвин» или «Рик» без нажатия кнопок.</span>
        </div>
    </div>
    <div class="loading" id="loader">⚡ Обработка на Helio X20...</div>
    <div class="input-bar">
        <button class="mic-btn" id="mic-btn" onclick="manualWakeUpDialogue()">🎤</button>
        <input type="text" id="prompt-input" placeholder="Скажи 'Мелвин' или 'Рик'..." onkeydown="if(event.key==='Enter') send()">
        <button onclick="send()">➤</button>
    </div>

    <script>
        const chatBox = document.getElementById('chat-box');
        const input = document.getElementById('prompt-input');
        const loader = document.getElementById('loader');
        const micBtn = document.getElementById('mic-btn');
        const personaBtn = document.getElementById('persona-btn');
        const headerTitle = document.getElementById('header-title');
        const vadIndicator = document.getElementById('vad-indicator');
        const vadText = document.getElementById('vad-text');

        // Audio Belch effect
        const burpAudio = new Audio('/burp.mp3');
        burpAudio.preload = 'auto';

        let currentPersona = localStorage.getItem('melvin_persona') || 'melvin';

        // Ultra-low pitch (More than an octave down: 0.40 bass)
        const TARGET_PITCH = 0.40;
        const TARGET_RATE = 0.95;

        let isBotSpeaking = false;
        let isWaitingForCommand = false;
        let dialogueActiveUntil = 0; // Timestamp when continuous multi-turn dialogue expires

        function onBotSpeechFinished() {
            console.log('[TTS] Speech finished. Applying 700ms acoustic cooldown buffer...');
            setTimeout(() => {
                isBotSpeaking = false;
                speechBuffer = [];
                preRollQueue = [];
                silenceCount = 0;
                maxRmsInPhrase = 0;

                // Continuous dialogue active for 25 seconds
                dialogueActiveUntil = Date.now() + 25000;
                isDialogueActive = true;

                // Play gentle ready earcon to notify user mic is listening for reply
                playEarcon('ready');

                // Short vibration pulse to signal mic is wide open for user command
                if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                    window.MelvinNativeBridge.vibrate(45);
                }

                vadIndicator.classList.add('dialogue-active');
                vadIndicator.classList.remove('recording');
                vadText.textContent = '⚡ ДИАЛОГ (25с): СЛУШАЮ...';
                console.log('[Dialogue] Bot speech done. Mic is OPEN for command!');
            }, 700);
        }

        function applyNativeVoiceSettings() {
            if (window.MelvinNativeBridge) {
                if (typeof window.MelvinNativeBridge.setPitch === 'function') {
                    window.MelvinNativeBridge.setPitch(TARGET_PITCH);
                }
                if (typeof window.MelvinNativeBridge.setRate === 'function') {
                    window.MelvinNativeBridge.setRate(TARGET_RATE);
                }
            }
        }
        applyNativeVoiceSettings();
        setTimeout(applyNativeVoiceSettings, 800);

        
        // ==========================================
        // ТАЙМЕРЫ И СЕКУНДОМЕР (Web Audio Alarm)
        // ==========================================
        let activeTimerInterval = null;
        let activeTimerSecondsLeft = 0;

        function formatTimerTime(totalSec) {
            const m = Math.floor(totalSec / 60);
            const s = totalSec % 60;
            return (m < 10 ? '0' + m : m) + ':' + (s < 10 ? '0' + s : s);
        }

        
        // ==========================================
        // XIAOMI SMART SPEAKER AMBIENT & SOUND SUITE
        // ==========================================
        let ambientAudioSource = null;
        let ambientGainNode = null;
        let ambientType = null;
        let nightClockInterval = null;

        function stopAmbientSound() {
            if (ambientAudioSource) {
                try { ambientAudioSource.stop(); } catch(e){}
                ambientAudioSource = null;
            }
            ambientType = null;
            if (ambientSleepInterval) {
                clearInterval(ambientSleepInterval);
                ambientSleepInterval = null;
            }
            const badge = document.getElementById('ambient-sound-badge');
            if (badge) badge.style.display = 'none';
        }

        function startAmbientSound(type, sleepSec) {
            stopAmbientSound();
            try {
                const ctx = window.__earconCtx || (window.__earconCtx = new (window.AudioContext || window.webkitAudioContext)());
                if (ctx.state === 'suspended') ctx.resume();

                const bufferSize = 2 * ctx.sampleRate;
                const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
                const output = noiseBuffer.getChannelData(0);

                let b0 = 0, b1 = 0, b2 = 0;
                for (let i = 0; i < bufferSize; i++) {
                    const white = Math.random() * 2 - 1;
                    if (type === 'rain' || type === 'fire') {
                        b0 = 0.99886 * b0 + white * 0.0555179;
                        b1 = 0.99332 * b1 + white * 0.0750759;
                        b2 = 0.96900 * b2 + white * 0.1538520;
                        output[i] = (b0 + b1 + b2) * 0.12;
                        if (type === 'fire' && Math.random() < 0.003) {
                            output[i] += (Math.random() * 0.6 - 0.3);
                        }
                    } else if (type === 'ocean') {
                        b0 = (b0 + (0.02 * white)) / 1.02;
                        output[i] = b0 * 0.35;
                    } else {
                        output[i] = white * 0.08;
                    }
                }

                const whiteNoise = ctx.createBufferSource();
                whiteNoise.buffer = noiseBuffer;
                whiteNoise.loop = true;

                const filter = ctx.createBiquadFilter();
                if (type === 'rain') {
                    filter.type = 'lowpass';
                    filter.frequency.setValueAtTime(1000, ctx.currentTime);
                } else if (type === 'ocean') {
                    filter.type = 'lowpass';
                    filter.frequency.setValueAtTime(450, ctx.currentTime);
                } else if (type === 'fire') {
                    filter.type = 'bandpass';
                    filter.frequency.setValueAtTime(650, ctx.currentTime);
                } else {
                    filter.type = 'lowpass';
                    filter.frequency.setValueAtTime(1500, ctx.currentTime);
                }

                const gain = ctx.createGain();
                gain.gain.setValueAtTime(0.35, ctx.currentTime);

                whiteNoise.connect(filter);
                filter.connect(gain);
                gain.connect(ctx.destination);

                whiteNoise.start(0);
                ambientAudioSource = whiteNoise;
                ambientGainNode = gain;
                ambientType = type;

                const badge = document.getElementById('ambient-sound-badge');
                const label = document.getElementById('ambient-sound-name');
                if (badge && label) {
                    const soundLabels = {rain: '🌧 Дождь', fire: '🔥 Костер', ocean: '🌊 Океан', whitenoise: '💤 Белый шум'};
                    const baseTitle = soundLabels[type] || 'Звук';
                    label.textContent = baseTitle;
                    badge.style.display = 'flex';

                    if (sleepSec && sleepSec > 0) {
                        let remaining = sleepSec;
                        ambientSleepInterval = setInterval(() => {
                            remaining--;
                            const m = Math.floor(remaining / 60);
                            const s = remaining % 60;
                            label.textContent = `${baseTitle} [${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}]`;
                            if (remaining <= 0) {
                                clearInterval(ambientSleepInterval);
                                ambientSleepInterval = null;
                                stopAmbientSound();
                            }
                        }, 1000);
                    }
                }
            } catch(e) {
                console.error('Ambient audio error:', e);
            }
        }

        
        // ==========================================
        // БУДИЛЬНИКИ И НАПОМИНАНИЯ (Web Audio Siren)
        // ==========================================
        let alarmSirenInterval = null;

        function startAlarmSound() {
            if (alarmSirenInterval) clearInterval(alarmSirenInterval);
            const playPulse = () => {
                try {
                    const ctx = window.__earconCtx || (window.__earconCtx = new (window.AudioContext || window.webkitAudioContext)());
                    if (ctx.state === 'suspended') ctx.resume();
                    for (let i = 0; i < 4; i++) {
                        const osc = ctx.createOscillator();
                        const gain = ctx.createGain();
                        osc.connect(gain);
                        gain.connect(ctx.destination);
                        const t = ctx.currentTime + i * 0.22;
                        osc.type = 'sawtooth';
                        osc.frequency.setValueAtTime(880, t);
                        osc.frequency.exponentialRampToValueAtTime(1760, t + 0.14);
                        gain.gain.setValueAtTime(0.35, t);
                        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.18);
                        osc.start(t);
                        osc.stop(t + 0.19);
                    }
                    if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                        window.MelvinNativeBridge.vibrate(600);
                    }
                } catch(e){}
            };
            playPulse();
            alarmSirenInterval = setInterval(playPulse, 1400);
        }

        function stopAlarmSound() {
            if (alarmSirenInterval) {
                clearInterval(alarmSirenInterval);
                alarmSirenInterval = null;
            }
        }

        function dismissAlarmUI() {
            stopAlarmSound();
            const ov = document.getElementById('alarmOverlay');
            if (ov) ov.style.display = 'none';
            appendMsg('bot', '⏰ Будильник выключен.');
        }

        function handleTriggeredAlert(alert) {
            if (alert.type === 'alarm') {
                const ov = document.getElementById('alarmOverlay');
                const tText = document.getElementById('alarmTimeText');
                const lText = document.getElementById('alarmLabelText');
                if (tText) tText.textContent = alert.time_str;
                if (lText) lText.textContent = alert.label || 'БУДИЛЬНИК';
                if (ov) ov.style.display = 'flex';
                startAlarmSound();
                const phrase = (currentPersona === 'rick') 
                    ? '*рыгает* Подъем, Морти! Звенит твой будильник на ' + alert.time_str + '! Хватит спать!'
                    : 'Внимание, кожаный ублюдок: время ' + alert.time_str + '. Сработал будильник. Пора просыпаться.';
                appendMsg('bot', '⏰ ' + phrase);
                speakWithLowPitch(phrase);
            } else if (alert.type === 'reminder') {
                const phrase = (currentPersona === 'rick')
                    ? '*рыгает* Эй, напоминаю: ' + alert.text + '!'
                    : 'Внимание! Напоминание: ' + alert.text + '.';
                appendMsg('bot', '🔔 ' + phrase);
                speakWithLowPitch(phrase);
                playEarcon('ready');
                if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                    window.MelvinNativeBridge.vibrate(400);
                }
            }
        }

        // Периодический опрос сработавших будильников и напоминаний (каждые 3.5 сек)
        setInterval(async () => {
            try {
                const res = await fetch('/api/organizer/poll');
                if (res.ok) {
                    const data = await res.json();
                    if (data.alerts && data.alerts.length > 0) {
                        for (const al of data.alerts) {
                            handleTriggeredAlert(al);
                        }
                    }
                }
            } catch(e){}
        }, 3500);

        function setNightlight(enable) {
            const ov = document.getElementById('nightlightOverlay');
            const clock = document.getElementById('nightClock');
            if (!ov) return;
            if (enable) {
                ov.style.display = 'flex';
                const updateClock = () => {
                    const now = new Date();
                    const h = String(now.getHours()).padStart(2, '0');
                    const m = String(now.getMinutes()).padStart(2, '0');
                    if (clock) clock.textContent = `${h}:${m}`;
                };
                updateClock();
                if (nightClockInterval) clearInterval(nightClockInterval);
                nightClockInterval = setInterval(updateClock, 1000);
                if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                    window.MelvinNativeBridge.vibrate(30);
                }
            } else {
                ov.style.display = 'none';
                if (nightClockInterval) {
                    clearInterval(nightClockInterval);
                    nightClockInterval = null;
                }
            }
        }

        // --- РАСШИРЕННЫЙ КАТАЛОГ РАДИОСТАНЦИЙ ---
        const RADIO_STATIONS = {
            lofi: { title: "Lofi Chill FM", genre: "Lofi / Downtempo", icon: "☕", url: "https://stream.zeno.fm/f3wvbbqmdg8uv" },
            synthwave: { title: "Nightride FM", genre: "Synthwave / 80s", icon: "⚡", url: "https://stream.nightride.fm/nightride.mp3" },
            rock: { title: "Indie Pop & Rock", genre: "Alternative Rock", icon: "🎸", url: "https://ice2.somafm.com/indiepop-128-mp3" },
            jazz: { title: "Secret Agent Jazz", genre: "Spy Jazz & Lounge", icon: "🎷", url: "https://ice1.somafm.com/secretagent-128-mp3" },
            ambient: { title: "Drone Zone", genre: "Deep Space Ambient", icon: "🌌", url: "https://ice1.somafm.com/dronezone-128-mp3" },
            classic: { title: "Radio Swiss Classic", genre: "Classical", icon: "🎻", url: "https://stream.srg-ssr.ch/m/rsc_de/mp3_128" },
            nashe: { title: "Наше Радио", genre: "Русский рок", icon: "📻", url: "https://nashe1.hostingradio.ru/nashe-128.mp3" }
        };
        const RADIO_KEYS = Object.keys(RADIO_STATIONS);
        let currentStationKey = 'lofi';
        let currentStationIndex = 0;
        let radioSleepInterval = null;
        let ambientSleepInterval = null;

        function renderRadioStationsList() {
            const container = document.getElementById('radioStationsList');
            if (!container) return;
            container.innerHTML = RADIO_KEYS.map(key => {
                const s = RADIO_STATIONS[key];
                const isActive = (key === currentStationKey && isRadioPlaying());
                return `
                    <div onclick="selectRadioStation('${key}')" style="background:${isActive ? 'rgba(233,30,99,0.18)' : 'rgba(255,255,255,0.04)'}; border:1px solid ${isActive ? '#e91e63' : 'rgba(255,255,255,0.08)'}; border-radius:8px; padding:10px 12px; display:flex; justify-content:space-between; align-items:center; cursor:pointer; transition:0.2s;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="font-size:20px;">${s.icon}</span>
                            <div>
                                <div style="font-weight:bold; font-size:13px; color:${isActive ? '#ff4081' : '#e6edf3'};">${s.title}</div>
                                <div style="font-size:11px; color:var(--text-dim);">${s.genre}</div>
                            </div>
                        </div>
                        <div>
                            ${isActive ? '<span style="color:#00ff9d; font-size:12px; font-weight:bold;">▶ ИГРАЕТ</span>' : '<span style="color:var(--text-dim); font-size:12px;">Включить</span>'}
                        </div>
                    </div>
                `;
            }).join('');
        }

        function isRadioPlaying() {
            const audio = document.getElementById('bgRadioAudio');
            return audio && !audio.paused && audio.src;
        }

        function toggleRadioModal() {
            const modal = document.getElementById('radioModal');
            if (!modal) return;
            if (modal.style.display === 'flex') {
                modal.style.display = 'none';
            } else {
                modal.style.display = 'flex';
                renderRadioStationsList();
            }
        }

        function selectRadioStation(key) {
            playRadio(key, 0);
            renderRadioStationsList();
            const s = RADIO_STATIONS[key];
            appendMsg('bot', `📻 Включена станция: ${s.icon} ${s.title} (${s.genre})`);
        }

        function playRadio(stationKey, sleepSec) {
            const audio = document.getElementById('bgRadioAudio');
            const badge = document.getElementById('radio-badge');
            const titleEl = document.getElementById('radio-station-title');
            if (!audio) return;

            if (stationKey && RADIO_STATIONS[stationKey]) {
                currentStationKey = stationKey;
                currentStationIndex = RADIO_KEYS.indexOf(stationKey);
            }
            const current = RADIO_STATIONS[currentStationKey] || RADIO_STATIONS['lofi'];

            if (audio.src !== current.url) {
                audio.src = current.url;
            }
            audio.volume = 0.6;
            audio.play().catch(e => console.log('Radio play error:', e));

            if (titleEl) titleEl.textContent = `${current.icon} ${current.title}`;
            if (badge) badge.style.display = 'flex';

            if (radioSleepInterval) {
                clearInterval(radioSleepInterval);
                radioSleepInterval = null;
            }

            if (sleepSec && sleepSec > 0) {
                let remaining = sleepSec;
                const sleepBadge = document.getElementById('radio-sleep-indicator');
                const updateSleepUI = () => {
                    const m = Math.floor(remaining / 60);
                    const s = remaining % 60;
                    if (sleepBadge) {
                        sleepBadge.textContent = `[${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}]`;
                        sleepBadge.style.display = 'inline';
                    }
                    if (remaining <= 0) {
                        clearInterval(radioSleepInterval);
                        radioSleepInterval = null;
                        // Плавное угасание громкости перед остановкой
                        let vol = audio.volume;
                        const fadeInterval = setInterval(() => {
                            vol = Math.max(0, vol - 0.15);
                            audio.volume = vol;
                            if (vol <= 0.05) {
                                clearInterval(fadeInterval);
                                stopRadio();
                            }
                        }, 300);
                    }
                    remaining--;
                };
                updateSleepUI();
                radioSleepInterval = setInterval(updateSleepUI, 1000);
            } else {
                const sleepBadge = document.getElementById('radio-sleep-indicator');
                if (sleepBadge) sleepBadge.style.display = 'none';
            }
        }

        function nextRadioStation() {
            currentStationIndex = (currentStationIndex + 1) % RADIO_KEYS.length;
            currentStationKey = RADIO_KEYS[currentStationIndex];
            playRadio(currentStationKey, 0);
            const cur = RADIO_STATIONS[currentStationKey];
            appendMsg('bot', `📻 Переключил волну: ${cur.icon} ${cur.title} (${cur.genre})`);
        }

        function stopRadio() {
            const audio = document.getElementById('bgRadioAudio');
            const badge = document.getElementById('radio-badge');
            const sleepBadge = document.getElementById('radio-sleep-indicator');
            if (audio) {
                audio.pause();
                audio.src = '';
            }
            if (badge) badge.style.display = 'none';
            if (sleepBadge) sleepBadge.style.display = 'none';
            if (radioSleepInterval) {
                clearInterval(radioSleepInterval);
                radioSleepInterval = null;
            }
        }

        function playCoinSound() {
            try {
                const ctx = window.__earconCtx || (window.__earconCtx = new (window.AudioContext || window.webkitAudioContext)());
                if (ctx.state === 'suspended') ctx.resume();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(1400, now);
                osc.frequency.exponentialRampToValueAtTime(1800, now + 0.05);
                osc.frequency.exponentialRampToValueAtTime(1200, now + 0.35);
                gain.gain.setValueAtTime(0.2, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
                osc.start(now);
                osc.stop(now + 0.45);
            } catch(e){}
        }

        function playDiceSound() {
            try {
                const ctx = window.__earconCtx || (window.__earconCtx = new (window.AudioContext || window.webkitAudioContext)());
                if (ctx.state === 'suspended') ctx.resume();
                for (let i = 0; i < 3; i++) {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    const t = ctx.currentTime + i * 0.08;
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(260 + i * 60, t);
                    gain.gain.setValueAtTime(0.25, t);
                    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.06);
                    osc.start(t);
                    osc.stop(t + 0.06);
                }
            } catch(e){}
        }

        function playFindPhoneAlarm() {
            try {
                const ctx = window.__earconCtx || (window.__earconCtx = new (window.AudioContext || window.webkitAudioContext)());
                if (ctx.state === 'suspended') ctx.resume();
                for (let i = 0; i < 5; i++) {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    const t = ctx.currentTime + i * 0.35;
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(600, t);
                    osc.frequency.exponentialRampToValueAtTime(1500, t + 0.25);
                    gain.gain.setValueAtTime(0.4, t);
                    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.32);
                    osc.start(t);
                    osc.stop(t + 0.33);
                }
                if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                    window.MelvinNativeBridge.vibrate(1200);
                }
            } catch(e){}
        }

        function handleTimerEvent(timer) {
            const badge = document.getElementById('active-timer-badge');
            const labelSpan = document.getElementById('timer-time-left');
            if (!badge || !labelSpan) return;

            if (timer.action === 'start') {
                if (activeTimerInterval) clearInterval(activeTimerInterval);
                activeTimerSecondsLeft = timer.duration_sec || 60;
                badge.style.display = 'flex';
                labelSpan.textContent = formatTimerTime(activeTimerSecondsLeft);
                
                activeTimerInterval = setInterval(() => {
                    activeTimerSecondsLeft--;
                    if (activeTimerSecondsLeft <= 0) {
                        clearInterval(activeTimerInterval);
                        activeTimerInterval = null;
                        badge.style.display = 'none';
                        playTimerAlarm();
                        const alertMsg = (currentPersona === 'rick') 
                            ? '*рыгает* Время вышло, Морти! Таймер сработал.'
                            : 'Внимание, кожаный ублюдок: время таймера истекло.';
                        appendMsg('bot', '⏱ ' + alertMsg);
                        speakWithLowPitch(alertMsg);
                    } else {
                        labelSpan.textContent = formatTimerTime(activeTimerSecondsLeft);
                    }
                }, 1000);
            } else if (timer.action === 'cancel') {
                if (activeTimerInterval) {
                    clearInterval(activeTimerInterval);
                    activeTimerInterval = null;
                }
                badge.style.display = 'none';
            }
        }

        function cancelTimerManual() {
            if (activeTimerInterval) {
                clearInterval(activeTimerInterval);
                activeTimerInterval = null;
                const badge = document.getElementById('active-timer-badge');
                if (badge) badge.style.display = 'none';
                appendMsg('bot', '⏱ Таймер остановлен вручную.');
            }
        }

        function playTimerAlarm() {
            try {
                const ctx = window.__earconCtx || (window.__earconCtx = new (window.AudioContext || window.webkitAudioContext)());
                if (ctx.state === 'suspended') ctx.resume();
                for (let i = 0; i < 4; i++) {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    const t = ctx.currentTime + i * 0.28;
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(880, t);
                    osc.frequency.setValueAtTime(1174.66, t + 0.12);
                    gain.gain.setValueAtTime(0.2, t);
                    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.24);
                    osc.start(t);
                    osc.stop(t + 0.25);
                }
                if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                    window.MelvinNativeBridge.vibrate(500);
                }
            } catch(e) {
                console.error('Alarm error:', e);
            }
        }

        function setScreenTorch(enable) {
            const ov = document.getElementById('screenTorchOverlay');
            if (!ov) return;
            if (enable) {
                ov.style.display = 'flex';
                if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                    window.MelvinNativeBridge.vibrate(50);
                }
            } else {
                ov.style.display = 'none';
                if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                    window.MelvinNativeBridge.vibrate(30);
                }
            }
        }

        function updatePersonaUI() {
            if (currentPersona === 'rick') {
                personaBtn.innerHTML = 'РИК';
                personaBtn.classList.add('rick-mode');
                if (headerTitle) headerTitle.textContent = 'РИК САНЧЕЗ // HELIO X20';
                input.placeholder = "Скажи 'Рик' или команду...";
                document.documentElement.style.setProperty('--accent', '#00e5ff');
                document.documentElement.style.setProperty('--accent-dim', 'rgba(0, 229, 255, 0.15)');
            } else {
                personaBtn.innerHTML = 'МЕЛВИН';
                personaBtn.classList.remove('rick-mode');
                if (headerTitle) headerTitle.textContent = 'МЕЛВИН // HELIO X20';
                input.placeholder = "Скажи 'Мелвин' или команду...";
                document.documentElement.style.setProperty('--accent', '#00ff9d');
                document.documentElement.style.setProperty('--accent-dim', 'rgba(0, 255, 157, 0.15)');
            }
        }
        updatePersonaUI();

        function togglePersona(force) {
            if (force) {
                currentPersona = force;
            } else {
                currentPersona = (currentPersona === 'melvin') ? 'rick' : 'melvin';
            }
            localStorage.setItem('melvin_persona', currentPersona);
            updatePersonaUI();
            fetch('/set_persona', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({persona: currentPersona})
            }).catch(e => console.log('Persona sync notice:', e));
        }

        function formatClockTime(d) {
            const date = d || new Date();
            const h = String(date.getHours()).padStart(2, '0');
            const m = String(date.getMinutes()).padStart(2, '0');
            return h + ':' + m;
        }

        function escapeHtml(str) {
            return (str || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
        }

        function appendMsg(role, text, timeSec, toolUsed) {
            const div = document.createElement('div');
            div.className = 'msg ' + (role === 'user' ? 'user' : 'bot');
            const timeStr = formatClockTime();
            
            if (role !== 'user') {
                let toolHtml = toolUsed ? '<div class="tool-badge">🔧 ' + toolUsed + '</div>' : '';
                let metaHtml = (timeSec ? '<span class="meta-tag">' + timeSec + 's</span>' : '') + '<span class="meta-tag" style="margin-left:6px; opacity:0.8;">' + timeStr + '</span>';
                let name = (currentPersona === 'rick') ? 'РИК САНЧЕЗ' : 'МЕЛВИН (ИИ)';
                div.innerHTML = '<div class="sender"><span>' + name + '</span>' + metaHtml + '</div>' + toolHtml + '<div>' + text + '</div>';
            } else {
                div.innerHTML = '<div>' + escapeHtml(text) + '</div><div style="font-size:10px; color:rgba(255,255,255,0.7); text-align:right; margin-top:4px; font-family:monospace;">' + timeStr + '</div>';
            }
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function send(explicitText) {
            const text = (explicitText || input.value).trim();
            if (!text) return;
            input.value = '';
            appendMsg('user', text);
            loader.style.display = 'block';
            let elapsedSec = 0;
            const name = (currentPersona === 'rick') ? 'Рик' : 'Мелвин';
            loader.textContent = name + ' думает на Helio X20... (0с)';
            const timer = setInterval(() => {
                elapsedSec++;
                loader.textContent = name + ' думает на Helio X20... (' + elapsedSec + 'с)';
            }, 1000);

            isSendingChat = true;
            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text, persona: currentPersona})
                });
                clearInterval(timer);
                loader.style.display = 'none';
                const data = await res.json();
                
                if (data.persona && data.persona !== currentPersona) {
                    currentPersona = data.persona;
                    localStorage.setItem('melvin_persona', currentPersona);
                    updatePersonaUI();
                }

                
                if (data.xiaomi) {
                    const x = data.xiaomi;
                    if (x.type === 'ambient_sound') {
                        if (x.action === 'play') startAmbientSound(x.sound, x.sleep_timer_sec);
                        else if (x.action === 'stop') stopAmbientSound();
                    } else if (x.type === 'nightlight') {
                        if (x.action === 'on') setNightlight(true);
                        else if (x.action === 'off') setNightlight(false);
                    } else if (x.type === 'radio') {
                        if (x.action === 'play') playRadio(x.station_key, x.sleep_timer_sec);
                        else if (x.action === 'next') nextRadioStation();
                        else if (x.action === 'stop') stopRadio();
                    } else if (x.type === 'coin_flip') {
                        playCoinSound();
                    } else if (x.type === 'dice_roll' || x.type === 'random_number') {
                        playDiceSound();
                    } else if (x.type === 'find_phone') {
                        playFindPhoneAlarm();
                    }
                }

                if (data.timer) {
                    handleTimerEvent(data.timer);
                }
                if (data.response) {
                    appendMsg('bot', data.response, data.inference_time_sec, data.tool_used);
                    if (data.tool_used === '!torch(1)' || data.torch === 1 || data.torch === 'ON') {
                        setScreenTorch(true);
                    } else if (data.tool_used === '!torch(0)' || data.torch === 0 || data.torch === 'OFF') {
                        const ov = document.getElementById('screenTorchOverlay');
                        if (ov) ov.style.display = 'none';
                    }
                    // If wake-word was hailed, bot is now waiting for user's command
                    if (data.tool_used === 'wake_word') {
                        isWaitingForCommand = true;
                    } else {
                        isWaitingForCommand = false;
                    }
                    speakWithLowPitch(data.response);
                } else {
                    appendMsg('bot', 'Ошибка: ' + (data.error || 'Процессор перегружен'));
                }
            } catch(e) {
                clearInterval(timer);
                loader.style.display = 'none';
                appendMsg('bot', 'Сбой соединения: ' + e);
            } finally {
                isSendingChat = false;
            }
        }

        // Синтезированные аппаратные звуковые сигналы (Earcons)
        function playEarcon(type) {
            try {
                const ctx = window.__earconCtx || (window.__earconCtx = new (window.AudioContext || window.webkitAudioContext)());
                if (ctx.state === 'suspended') ctx.resume();

                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);

                const now = ctx.currentTime;

                if (type === 'ready') {
                    // Индикационный сигнал готовности слушать (вопрос/команда)
                    if (currentPersona === 'rick') {
                        // Футуристичный свист пушки Рика
                        osc.type = 'sawtooth';
                        osc.frequency.setValueAtTime(320, now);
                        osc.frequency.exponentialRampToValueAtTime(780, now + 0.12);
                        gain.gain.setValueAtTime(0.09, now);
                        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
                        osc.start(now);
                        osc.stop(now + 0.14);
                    } else {
                        // Чистый кибернетический двойной пинг Мелвина
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(587, now);
                        osc.frequency.setValueAtTime(880, now + 0.06);
                        gain.gain.setValueAtTime(0.12, now);
                        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
                        osc.start(now);
                        osc.stop(now + 0.15);
                    }
                    if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                        window.MelvinNativeBridge.vibrate(35);
                    }
                } else if (type === 'done_listening') {
                    // Сигнал окончания записи ("Закончил слушать, думаю...")
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(720, now);
                    osc.frequency.exponentialRampToValueAtTime(360, now + 0.08);
                    gain.gain.setValueAtTime(0.09, now);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);
                    osc.start(now);
                    osc.stop(now + 0.09);
                    if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                        window.MelvinNativeBridge.vibrate(20);
                    }
                }
            } catch(e) {
                console.log('Earcon notice:', e);
            }
        }

        function playSpecialSound(url, callback) {
            try {
                const snd = new Audio(url);
                snd.onended = () => { if (callback) callback(); };
                snd.onerror = () => { if (callback) callback(); };
                const p = snd.play();
                if (p !== undefined) p.catch(() => { if (callback) callback(); });
            } catch(e) {
                if (callback) callback();
            }
        }

        function playBurpSound(callback) {
            try {
                burpAudio.currentTime = 0;
                burpAudio.onended = () => { if (callback) callback(); };
                burpAudio.onerror = () => { if (callback) callback(); };
                const p = burpAudio.play();
                if (p !== undefined) p.catch(() => { if (callback) callback(); });
            } catch(e) {
                if (callback) callback();
            }
        }

        function speakWithLowPitch(text) {
            let raw = text.trim();
            if (!raw) return;

            // Сброс предыдущего сторожевого таймера
            if (window.__speechWatchdog) clearTimeout(window.__speechWatchdog);

            isBotSpeaking = true;
            speechBuffer = [];
            preRollQueue = [];
            silenceCount = 0;
            maxRmsInPhrase = 0;

            // Сторожевой таймер безопасности (макс 10 секунд): размораживает микрофон при любом сбое
            window.__speechWatchdog = setTimeout(() => {
                if (isBotSpeaking) {
                    console.log('[Watchdog] Resetting stuck isBotSpeaking state');
                    onBotSpeechFinished();
                }
            }, 10000);

            vadIndicator.classList.remove('recording', 'dialogue-active');
            vadText.textContent = (currentPersona === 'rick') ? 'РИК ГОВОРИТ...' : 'МЕЛВИН ГОВОРИТ...';

            const hasBurp = /\*рыгает\*|\*отрыжка\*/i.test(raw);
            const hasPortal = /\[portal_gun\]|\*портал\*/i.test(raw);
            const hasWubba = /\[wubba_lubba\]/i.test(raw);
            const hasPickle = /\[pickle_rick\]/i.test(raw);

            let cleanText = raw
                .replace(/\*рыгает\*|\*отрыжка\*/gi, '')
                .replace(/\[portal_gun\]|\*портал\*/gi, '')
                .replace(/\[wubba_lubba\]/gi, '')
                .replace(/\[pickle_rick\]/gi, '')
                .trim();

            if (hasBurp) {
                playBurpSound(() => executeVoiceOutput(cleanText));
            } else if (hasPortal) {
                playSpecialSound('/sound/portal_gun.mp3', () => executeVoiceOutput(cleanText));
            } else if (hasWubba) {
                playSpecialSound('/sound/wubba_lubba.mp3', () => executeVoiceOutput(cleanText));
            } else if (hasPickle) {
                playSpecialSound('/sound/pickle_rick.mp3', () => executeVoiceOutput(cleanText));
            } else {
                executeVoiceOutput(cleanText);
            }
        }

        function executeVoiceOutput(spoken) {
            const isRick = (currentPersona === 'rick');
            // Естественные, разборчивые и низкие настройки для Google TTS
            const targetPitch = isRick ? 0.88 : 0.80;
            const targetRate = isRick ? 1.06 : 0.94;

            if (window.MelvinNativeBridge) {
                try {
                    if (typeof window.MelvinNativeBridge.setPitch === 'function') {
                        window.MelvinNativeBridge.setPitch(targetPitch);
                    }
                    if (typeof window.MelvinNativeBridge.setSpeechRate === 'function') {
                        window.MelvinNativeBridge.setSpeechRate(targetRate);
                    } else if (typeof window.MelvinNativeBridge.setRate === 'function') {
                        window.MelvinNativeBridge.setRate(targetRate);
                    }
                } catch(e) {
                    console.log('Bridge config error:', e);
                }
            }

            // Очистка от служебных меток, prompt-leak и артефактов
            let cleanSpeech = spoken
                .replace(/\*.*?\*/g, '')
                .replace(/\b(\d+\s+)?(коротк\w+|язвительн\w+|предложени\w+|инструкци\w+|строго\s+1)\b.*/gi, '')
                .replace(/\s+([.,!?:;])/g, '$1')
                .trim();
            if (!cleanSpeech) cleanSpeech = "Слушаю.";

            const words = cleanSpeech.split(/\s+/).filter(Boolean);
            const speechDurationMs = Math.max(1600, Math.round(words.length * 420 + 900));

            // Приоритет 1: Нативный мост приложения (Google Text-to-Speech на Android)
            // Мгновенный отклик (0 мс), чистый русский голос, никакой каши и тормозов
            if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.speak === 'function') {
                try {
                    window.MelvinNativeBridge.speak(cleanSpeech);
                    setTimeout(onBotSpeechFinished, speechDurationMs);
                    return;
                } catch(e) {
                    console.log('Native bridge speak notice:', e);
                }
            }

            // Приоритет 2: Web Speech API (встроенный синтез браузера / WebView)
            if ('speechSynthesis' in window) {
                try {
                    window.speechSynthesis.cancel();
                    const utter = new SpeechSynthesisUtterance(cleanSpeech);
                    utter.lang = 'ru-RU';
                    utter.rate = targetRate;
                    utter.pitch = targetPitch;

                    const voices = window.speechSynthesis.getVoices();
                    const ruMale = voices.find(v => v.lang.startsWith('ru') && (
                        v.name.includes('Male') || v.name.includes('Yuri') || v.name.includes('Pavel') ||
                        v.name.includes('Dmitry') || v.name.includes('Alexander')
                    )) || voices.find(v => v.lang.startsWith('ru'));
                    if (ruMale) utter.voice = ruMale;

                    utter.onend = onBotSpeechFinished;
                    utter.onerror = (e) => {
                        console.log('SpeechSynthesis error:', e);
                        onBotSpeechFinished();
                    };
                    window.speechSynthesis.speak(utter);
                    return;
                } catch(e) {
                    console.log('SpeechSynthesis notice:', e);
                }
            }

            // Приоритет 3: Серверный DSP-аудиопоток (/api/tts) при отсутствии Google TTS
            const ttsUrl = '/api/tts?text=' + encodeURIComponent(spoken) + '&persona=' + encodeURIComponent(currentPersona);
            const neuralAudio = new Audio(ttsUrl);
            neuralAudio.onended = onBotSpeechFinished;
            neuralAudio.onerror = () => {
                setTimeout(onBotSpeechFinished, speechDurationMs);
            };
            neuralAudio.play().catch(() => {
                setTimeout(onBotSpeechFinished, speechDurationMs);
            });
        }

        // ========================================================
        // 100% HANDS-FREE CONTINUOUS MICROPHONE LISTENER (ZERO BUTTONS!)
        // ========================================================
        // Качественный антиалиасинг-ресемплер (48000/44100 Гц -> 16000 Гц)
        function resampleTo16k(audioBuffer, fromSampleRate) {
            if (!audioBuffer || audioBuffer.length === 0) return new Float32Array(0);
            if (fromSampleRate === 16000) return audioBuffer;

            const ratio = fromSampleRate / 16000;
            const newLength = Math.round(audioBuffer.length / ratio);
            const result = new Float32Array(newLength);
            let offsetResult = 0;
            let offsetBuffer = 0;

            while (offsetResult < result.length) {
                const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
                let accum = 0;
                let count = 0;
                for (let i = offsetBuffer; i < nextOffsetBuffer && i < audioBuffer.length; i++) {
                    accum += audioBuffer[i];
                    count++;
                }
                result[offsetResult] = count > 0 ? (accum / count) : audioBuffer[offsetBuffer];
                offsetResult++;
                offsetBuffer = nextOffsetBuffer;
            }
            return result;
        }

        function encodeWAV(samples, sampleRate) {
            const buffer = new ArrayBuffer(44 + samples.length * 2);
            const view = new DataView(buffer);

            function writeString(offset, string) {
                for (let i = 0; i < string.length; i++) {
                    view.setUint8(offset + i, string.charCodeAt(i));
                }
            }

            writeString(0, 'RIFF');
            view.setUint32(4, 36 + samples.length * 2, true);
            writeString(8, 'WAVE');
            writeString(12, 'fmt ');
            view.setUint32(16, 16, true);
            view.setUint16(20, 1, true); // PCM
            view.setUint16(22, 1, true); // Mono
            view.setUint32(24, sampleRate, true);
            view.setUint32(28, sampleRate * 2, true);
            view.setUint16(32, 2, true);
            view.setUint16(34, 16, true);
            writeString(36, 'data');
            view.setUint32(40, samples.length * 2, true);

            let offset = 44;
            for (let i = 0; i < samples.length; i++, offset += 2) {
                const s = Math.max(-1, Math.min(1, samples[i]));
                view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
            }
            return new Blob([buffer], { type: 'audio/wav' });
        }

        let audioStream = null;
        let audioContext = null;
        let isCapturingSpeech = false;
        let speechBuffer = [];
        let silenceCount = 0;
        let maxRmsInPhrase = 0;
        const PRE_ROLL_CHUNKS = 3; // ~750ms pre-speech audio buffer
        let preRollQueue = [];
        let isTranscribing = false;
        let isSendingChat = false;

        async function initHandsFreeWakeWord() {
            try {
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    vadText.textContent = 'МИКРОФОН НЕДОСТУПЕН';
                    return;
                }

                audioStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

                // Создаем контекст без принудительного sampleRate (берем аппаратную частоту устройства)
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const source = audioContext.createMediaStreamSource(audioStream);
                const processor = audioContext.createScriptProcessor(4096, 1, 1);
                
                // Маршрут через gain=0 во избежание акустической петли
                const zeroGain = audioContext.createGain();
                zeroGain.gain.value = 0;

                source.connect(processor);
                processor.connect(zeroGain);
                zeroGain.connect(audioContext.destination);

                processor.onaudioprocess = (e) => {
                    if (isBotSpeaking || isTranscribing || isSendingChat) {
                        speechBuffer = [];
                        silenceCount = 0;
                        maxRmsInPhrase = 0;
                        return;
                    }

                    const inputData = e.inputBuffer.getChannelData(0);
                    let sum = 0;
                    for (let i = 0; i < inputData.length; i++) {
                        sum += inputData[i] * inputData[i];
                    }
                    const rms = Math.sqrt(sum / inputData.length);

                    const isDialogueActive = Date.now() < dialogueActiveUntil;
                    // Пороги VAD: 0.024 в ожидании (отсекаем комнатный шум/шорохи), 0.016 в активном диалоге
                    const currentThreshold = isDialogueActive ? 0.016 : 0.024;

                    if (rms > currentThreshold) {
                        silenceCount = 0;
                        if (!isCapturingSpeech) {
                            isCapturingSpeech = true;
                            speechBuffer = [];
                            maxRmsInPhrase = rms;
                            for (let p of preRollQueue) {
                                speechBuffer.push(p);
                            }
                            vadIndicator.classList.add('recording');
                            vadText.textContent = isDialogueActive ? 'СЛУШАЮ КОМАНДУ...' : 'ЗАПИСЬ РЕЧИ...';
                        } else {
                            if (rms > maxRmsInPhrase) maxRmsInPhrase = rms;
                        }
                    } else if (isCapturingSpeech) {
                        silenceCount++;
                    } else {
                        preRollQueue.push(new Float32Array(inputData));
                        if (preRollQueue.length > PRE_ROLL_CHUNKS) {
                            preRollQueue.shift();
                        }
                    }

                    if (isCapturingSpeech) {
                        speechBuffer.push(new Float32Array(inputData));

                        // Завершение реплики:
                        // В диалоге: 10 чанков тишины (~0.85s) или макс 35 чанков (~3s)
                        // В ожидании: 8 чанков тишины (~0.7s) или макс 24 чанка (~2s)
                        const maxSilence = isDialogueActive ? 10 : 8;
                        const maxBuffer = isDialogueActive ? 35 : 24;

                        if (silenceCount >= maxSilence || speechBuffer.length >= maxBuffer) {
                            isCapturingSpeech = false;
                            vadIndicator.classList.remove('recording');

                            const captured = speechBuffer;
                            speechBuffer = [];
                            preRollQueue = [];
                            const peak = maxRmsInPhrase;
                            maxRmsInPhrase = 0;

                            // В режиме ожидания отсекаем короткие щелчки/шумы (< 6 чанков ~0.5s или пик < 0.026)
                            const minChunks = isDialogueActive ? 4 : 6;
                            const minPeak = isDialogueActive ? 0.018 : 0.026;

                            if (captured.length >= minChunks && peak >= minPeak) {
                                vadText.textContent = '⚡ ОБРАБОТКА...';
                                // ВАЖНО: Звук "пульк" (done_listening) играем ТОЛЬКО в активном диалоге!
                                // В режиме ожидания при фоновых звуках телефон остается ПОЛНОСТЬЮ БЕСШУМНЫМ!
                                if (isDialogueActive) {
                                    playEarcon('done_listening');
                                }

                                let totalLen = 0;
                                for (let b of captured) totalLen += b.length;
                                const flat = new Float32Array(totalLen);
                                let off = 0;
                                for (let b of captured) {
                                    flat.set(b, off);
                                    off += b.length;
                                }

                                processSpeechChunk(flat, isDialogueActive);
                            } else {
                                console.log('[Hands-Free] Discarded noise/too short:', captured.length, 'chunks, peak RMS:', peak, '| Dialogue:', isDialogueActive);
                                if (isDialogueActive) {
                                    vadIndicator.classList.add('dialogue-active');
                                    vadText.textContent = 'ДИАЛОГ: ГОВОРИТЕ...';
                                } else {
                                    vadIndicator.classList.remove('dialogue-active');
                                    vadText.textContent = 'СЛУШАЮ: "МЕЛВИН / РИК"';
                                }
                            }
                        }
                    } else {
                        if (isDialogueActive) {
                            vadIndicator.classList.add('dialogue-active');
                        } else {
                            vadIndicator.classList.remove('dialogue-active');
                        }
                    }
                };

                vadText.textContent = 'СЛУШАЮ: "МЕЛВИН / РИК"';
                console.log('[Hands-Free] Mic listener running continuously!');
            } catch(e) {
                console.log('[Hands-Free] Mic init error:', e);
                vadText.textContent = 'ОШИБКА МИКРОФОНА';
            }
        }

        let isDialogueActive = false;

        // Таймер обратного отсчета 30 секунд
        setInterval(() => {
            if (isBotSpeaking) return;
            const remainingMs = dialogueActiveUntil - Date.now();
            if (remainingMs > 0) {
                isDialogueActive = true;
                const sec = Math.ceil(remainingMs / 1000);
                vadIndicator.classList.add('dialogue-active');
                vadIndicator.classList.remove('recording');
                vadText.textContent = `⚡ ДИАЛОГ (${sec}с): СЛУШАЮ...`;
            } else if (isDialogueActive) {
                isDialogueActive = false;
                dialogueActiveUntil = 0;
                vadIndicator.classList.remove('dialogue-active', 'recording');
                vadText.textContent = 'ЖДУ ОКЛИК: "МЕЛВИН" / "РИК"';
                console.log('[Hands-Free] Timeout elapsed. Switched to Standby.');
            }
        }, 500);

        function cleanWakeWords(rawText) {
            return rawText
                .replace(/^(?:эй|слушай|привет|ок)?\s*(?:мелвин|мэлвин|melvin|рик|rick)[,\s]*/i, '')
                .trim();
        }

        async function processSpeechChunk(samples, wasDialogue) {
            if (isTranscribing) return;
            isTranscribing = true;
            try {
                const hardwareRate = (audioContext && audioContext.sampleRate) ? audioContext.sampleRate : 48000;
                const resampled = resampleTo16k(samples, hardwareRate);
                const wavBlob = encodeWAV(resampled, 16000);

                const res = await fetch('/transcribe_audio', {
                    method: 'POST',
                    body: wavBlob
                });
                const data = await res.json();

                if (data.status === 'ok' && data.text) {
                    const text = data.text.trim();
                    const lower = text.toLowerCase();
                    console.log('[Hands-Free] Recognized speech:', text, '| wasDialogue:', wasDialogue);

                    // Отсеиваем галлюцинации Whisper на тишине/шорохах
                    if (text.length < 2 || /^[\s.,!?;:\-_'"]+$/.test(text) ||
                        /^(субтитры|продолжение следует|спасибо за просмотр|редактор|неразборчиво|музыка|аплодисменты)/i.test(text)) {
                        console.log('[Hands-Free] Discarded noise hallucination:', text);
                        return;
                    }

                    const hasMelvin = lower.includes('мелвин') || lower.includes('мэлвин') || lower.includes('melvin');
                    const hasRick = lower.includes('рик') || lower.includes('rick');
                    const hasStop = lower.includes('стоп') || lower.includes('хватит') || lower.includes('отмена') || lower.includes('заткнись');

                    // 1. Команда принудительного выхода из диалога
                    if (hasStop) {
                        dialogueActiveUntil = 0;
                        isDialogueActive = false;
                        appendMsg('user', text);
                        appendMsg('bot', 'Диалог завершен. Перехожу в режим ожидания оклика.');
                        vadIndicator.classList.remove('dialogue-active', 'recording');
                        vadText.textContent = 'ЖДУ ОКЛИК: "МЕЛВИН" / "РИК"';
                        return;
                    }

                    // 2. РЕЖИМ ОЖИДАНИЯ (СТЕНДБАЙ): реагируем ТОЛЬКО на "Мелвин" или "Рик"
                    if (!wasDialogue) {
                        if (!hasMelvin && !hasRick) {
                            console.log('[Hands-Free Standby] Ignored speech without wake-word:', text);
                            vadIndicator.classList.remove('dialogue-active', 'recording');
                            vadText.textContent = 'ЖДУ ОКЛИК: "МЕЛВИН" / "РИК"';
                            return;
                        }

                        // Активация Мелвина
                        if (hasMelvin) {
                            togglePersona('melvin');
                            dialogueActiveUntil = Date.now() + 30000;
                            isDialogueActive = true;
                            playEarcon('ready'); // Двойной кибер-пинг готовности
                            if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                                window.MelvinNativeBridge.vibrate(40);
                            }
                            const cmd = cleanWakeWords(text);
                            if (cmd) {
                                send(cmd);
                            } else {
                                vadIndicator.classList.add('dialogue-active');
                                vadText.textContent = '⚡ ДИАЛОГ (30с): СЛУШАЮ...';
                                appendMsg('bot', 'Слушаю тебя, кожаный ублюдок. Выкладывай.');
                                speakWithLowPitch('Слушаю тебя. Выкладывай.');
                            }
                            return;
                        }

                        // Активация Рика
                        if (hasRick) {
                            togglePersona('rick');
                            dialogueActiveUntil = Date.now() + 30000;
                            isDialogueActive = true;
                            playEarcon('ready'); // Портальный звук Рика
                            if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                                window.MelvinNativeBridge.vibrate(40);
                            }
                            const cmd = cleanWakeWords(text);
                            if (cmd) {
                                send(cmd);
                            } else {
                                vadIndicator.classList.add('dialogue-active');
                                vadText.textContent = '⚡ ДИАЛОГ (30с): СЛУШАЮ...';
                                appendMsg('bot', '*рыгает* Да, я слушаю, Морти. Говори быстрее.');
                                speakWithLowPitch('*рыгает* Да, я слушаю. Чего надо?');
                            }
                            return;
                        }
                    }

                    // 3. РЕЖИМ АКТИВНОГО ДИАЛОГА (30 СЕКУНД):
                    // Переключаем персону, если назвали другое имя
                    if (hasRick && currentPersona !== 'rick') {
                        togglePersona('rick');
                    } else if (hasMelvin && currentPersona !== 'melvin') {
                        togglePersona('melvin');
                    }

                    // Продлеваем активный диалог еще на 25 секунд
                    dialogueActiveUntil = Date.now() + 25000;
                    isDialogueActive = true;

                    const msgToSend = cleanWakeWords(text) || text;
                    send(msgToSend);

                } else {
                    if (isDialogueActive) {
                        const sec = Math.max(1, Math.ceil((dialogueActiveUntil - Date.now()) / 1000));
                        vadText.textContent = `⚡ ДИАЛОГ (${sec}с): СЛУШАЮ...`;
                    } else {
                        vadText.textContent = 'ЖДУ ОКЛИК: "МЕЛВИН" / "РИК"';
                    }
                }
            } catch(e) {
                console.log('[Hands-Free] STT error:', e);
            } finally {
                isTranscribing = false;
            }
        }

        // Start hands-free listener on load
        window.addEventListener('load', () => {
            initHandsFreeWakeWord();
        });

        // Fallback manual trigger for Google dialog if user taps mic button
        function manualWakeUpDialogue() {
            dialogueActiveUntil = Date.now() + 30000;
            isDialogueActive = true;
            playEarcon('ready');
            if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                window.MelvinNativeBridge.vibrate(45);
            }
            vadIndicator.classList.add('dialogue-active');
            vadIndicator.classList.remove('recording');
            vadText.textContent = '⚡ ДИАЛОГ (30с): СЛУШАЮ...';
            console.log('[Hands-Free] Manually activated 30s dialogue window');
        }

        window.onNativeVoiceInput = function(text) {
            send(text);
        };
    
        // --- ЗАМЕТКИ И МЫСЛИ (UI HANDLERS) ---
        async function toggleNotesModal() {
            const modal = document.getElementById('notesModal');
            if (!modal) return;
            if (modal.style.display === 'flex') {
                modal.style.display = 'none';
            } else {
                modal.style.display = 'flex';
                await loadNotesList();
            }
        }

        async function loadNotesList() {
            const container = document.getElementById('notesListContainer');
            if (!container) return;
            try {
                const res = await fetch('/api/notes');
                const data = await res.json();
                if (data.status === 'ok' && data.notes && data.notes.length > 0) {
                    container.innerHTML = data.notes.map(n => `
                        <div style="background:rgba(255,255,255,0.04); border-left:3px solid #ffb74d; border-radius:6px; padding:8px 10px; display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
                            <div style="flex:1;">
                                <div style="font-size:10px; color:#ffb74d; font-family:monospace; margin-bottom:3px;">${n.created_at}</div>
                                <div style="font-size:13px; color:#e6edf3; line-height:1.3;">${n.content}</div>
                            </div>
                            <div style="display:flex; gap:6px; align-items:center;">
                                <button onclick="deleteNoteUI(${n.id})" style="background:none; border:none; color:#ff5252; cursor:pointer; font-size:14px; padding:2px 4px;" title="Удалить">🗑</button>
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div style="color:var(--text-dim); font-size:13px; text-align:center; padding:30px 0;">Архив заметок пуст.<br><span style="font-size:11px; opacity:0.8;">Скажи: «Мелвин, запиши мысль [текст]»</span></div>';
                }
            } catch(e) {
                container.innerHTML = '<div style="color:#ff5252; font-size:13px; text-align:center;">Ошибка загрузки заметок</div>';
            }
        }

        async function deleteNoteUI(id) {
            try {
                await fetch('/api/notes', {
                    method: 'DELETE',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id: id})
                });
                await loadNotesList();
            } catch(e){}
        }

        async function clearAllNotesUI() {
            if (!confirm('Точно удалить все заметки из архива?')) return;
            try {
                await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: 'очисти все заметки', persona: currentPersona})
                });
                await loadNotesList();
            } catch(e){}
        }

    </script>
</body>
</html>
"""

# ==========================================
# 5. БАЗА ДАННЫХ И ПАМЯТЬ (FTS5 Trigram)
# ==========================================
def init_db():
    try:
        knowledge_rag.init_knowledge_db()
    except Exception as e:
        print(f'RAG init notice: {e}')
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS memory_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            role TEXT,
            content TEXT
        )
    """)
    try:
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='dialog_fts'")
        row = cur.fetchone()
        if row and "trigram" not in row[0]:
            cur.execute("DROP TABLE IF EXISTS dialog_fts")
    except Exception:
        pass

    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS dialog_fts USING fts5(
            role,
            content,
            timestamp,
            tokenize='trigram'
        )
    """)
    conn.commit()
    conn.close()

def save_memory(role, content):
    try:
        now = time.time()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO memory_log (timestamp, role, content) VALUES (?, ?, ?)", (now, role, content))
        cur.execute("INSERT INTO dialog_fts (role, content, timestamp) VALUES (?, ?, ?)", (role, content, str(now)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

def search_relevant_memories(query, max_results=2):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        clean_q = re.sub(r'[^а-яА-Яa-zA-Z0-9\s]', ' ', query).strip()
        words = [w for w in clean_q.split() if len(w) >= 3]
        if not words:
            conn.close()
            return []
        
        match_clause = " OR ".join([f'"{w}"' for w in words[:3]])
        cur.execute("""
            SELECT content FROM dialog_fts 
            WHERE dialog_fts MATCH ? 
            ORDER BY rank 
            LIMIT ?
        """, (match_clause, max_results))
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        print(f"FTS Search notice: {e}")
        return []

# ==========================================
# 6. ОПРОС ИНТЕНТОВ ОБОРУДОВАНИЯ
# ==========================================
def check_fast_tools(user_msg, persona="melvin"):
    msg_lower = user_msg.lower()
    tool_name = None
    telemetry_phrase = ""
    canned_answer = None
    replies = TOOL_CANNED_REPLIES.get(persona, TOOL_CANNED_REPLIES["melvin"])

    # 1. Flashlight
    is_torch_on = any(w in msg_lower for w in [
        "фонарик", "посвети", "подсвети", "включи свет", "вруби свет", "зажги",
        "темно", "тут темно", "ничего не видно", "не видно ни зги", "сделай светлее",
        "освети", "вруби иллюминацию", "дай свет", "свет включи", "свет зажги"
    ])
    is_torch_off = any(w in msg_lower for w in [
        "выключи", "погаси", "выруби", "отключи", "погаси свет", "выруби свет",
        "погаси иллюминацию", "хватит светить", "выключи фонарик", "выруби фонарик",
        "не свети", "темноту верни", "темноту включи", "свет выключи"
    ])

    if is_torch_off:
        tool_name = "!torch(0)"
        phone_tools.toggle_torch(0)
        telemetry_phrase = "Фонарик выключен."
        canned_answer = replies["!torch(0)"]
    elif is_torch_on:
        tool_name = "!torch(1)"
        phone_tools.toggle_torch(1)
        telemetry_phrase = "Фонарик включен на полную мощность."
        canned_answer = replies["!torch(1)"]
    # 2. Battery
    elif any(w in msg_lower for w in ["батаре", "заряд", "процент", "аккумулятор", "питание"]):
        tool_name = "!bat()"
        bat = phone_tools.get_battery()
        telemetry_phrase = f"Заряд батареи: {bat.get('battery')}, температура: {bat.get('temp')}."
        canned_answer = replies["!bat()"].format(
            battery=bat.get('battery', 'N/A'),
            temp=bat.get('temp', 'N/A')
        )
    # 3. CPU & RAM
    elif any(w in msg_lower for w in ["температур", "памят", "проц", "нагрузк", "железо", "чип", "helio", "cpu"]):
        tool_name = "!sys()"
        stat = phone_tools.get_hardware_status()
        avail_ram = stat.get('ram_available') or stat.get('mem_available') or "N/A"
        telemetry_phrase = f"Температура CPU: {stat.get('cpu_temp')}, память: {avail_ram} свободно."
        canned_answer = replies["!sys()"].format(
            cpu_temp=stat.get('cpu_temp', 'N/A'),
            ram=avail_ram
        )
    # 4. Live Weather
    elif any(w in msg_lower for w in ["погод", "на улице", "за бортом", "дождь", "холодно", "жарко", "градус"]):
        tool_name = "!weather()"
        w_data = get_live_weather()
        if w_data.get("status") == "ok":
            telemetry_phrase = f"Погода: {w_data['desc']}, {w_data['temp']}°C, ветер {w_data['wind']} км/ч."
            canned_answer = replies["!weather()"].format(
                temp=w_data['temp'],
                desc=w_data['desc'],
                humidity=w_data['humidity'],
                wind=w_data['wind']
            )
        else:
            canned_answer = "*рыгает* Спутники врут, но жить пока можно." if persona == "rick" else "Связь со спутниками сбоит, но твоя планета всё ещё пригодна для жизни."

    is_direct_command = len(user_msg.split()) <= 8
    return tool_name, telemetry_phrase, (canned_answer if is_direct_command else None)

# ==========================================
# 7. МАРШРУТЫ FLASK
# ==========================================
@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/sound/<path:filename>", methods=["GET"])
def get_sound_clip(filename):
    clean_name = os.path.basename(filename)
    candidates = [
        f"/sdcard/melvin/{clean_name}",
        f"/melvin/{clean_name}",
        f"melvin_src/{clean_name}",
        clean_name
    ]
    for p in candidates:
        if os.path.exists(p):
            mimetype = "audio/mpeg" if p.endswith(".mp3") else "audio/wav"
            return send_file(p, mimetype=mimetype)
    return ("Sound not found", 404)

@app.route("/burp.mp3", methods=["GET"])
def get_burp_audio():
    for p in BURP_PATHS:
        if os.path.exists(p):
            return send_file(p, mimetype="audio/mpeg")
    return ("Audio file not found", 404)

@app.route("/api/tts", methods=["GET", "POST"])
def api_tts():
    text = request.args.get("text") or (request.get_json(silent=True) or {}).get("text", "")
    persona = request.args.get("persona") or (request.get_json(silent=True) or {}).get("persona", "") or CURRENT_PERSONA
    if not text:
        return ("Empty text", 400)
    bio = rick_voice.voice_engine.synthesize_to_memory(text, persona=persona)
    bio.seek(0)
    return send_file(bio, mimetype="audio/wav", as_attachment=False, download_name="voice.wav")

@app.route("/persona", methods=["GET"])
def get_persona():
    return jsonify({"persona": CURRENT_PERSONA})

@app.route("/set_persona", methods=["POST"])
def set_persona():
    global CURRENT_PERSONA
    data = request.get_json(force=True, silent=True) or {}
    p = data.get("persona", "").lower()
    if p in ["melvin", "rick"]:
        CURRENT_PERSONA = p
    return jsonify({"status": "ok", "persona": CURRENT_PERSONA})

@app.route("/transcribe_audio", methods=["POST"])
def transcribe_audio():
    t_start = time.time()
    try:
        audio_data = request.get_data()
        if not audio_data or len(audio_data) < 4000:
            return jsonify({"status": "empty", "text": ""})
        
        wav_len = len(audio_data) - 44
        duration = max(0.1, wav_len / 32000.0)
        
        try:
            debug_wav = "/melvin/last_stt_debug.wav" if os.path.exists("/melvin") else "/sdcard/melvin/last_stt_debug.wav"
            with open(debug_wav, "wb") as f_dbg:
                f_dbg.write(audio_data)
        except Exception:
            pass
        
        buf = io.BytesIO(audio_data)
        with sr.AudioFile(buf) as source:
            audio = speech_rec.record(source)
            
        text = speech_rec.recognize_google(audio, language="ru-RU")
        dt = round(time.time() - t_start, 2)
        print(f"[Hands-Free STT] ({duration:.1f}s audio in {dt}s) Recognized: '{text}'")
        return jsonify({"status": "ok", "text": text, "duration": duration})
    except sr.UnknownValueError:
        dt = round(time.time() - t_start, 2)
        print(f"[Hands-Free STT] ({duration:.1f}s audio in {dt}s) No speech detected (silence/noise)")
        return jsonify({"status": "no_speech", "text": ""})
    except Exception as e:
        print(f"[Hands-Free STT error]: {e}")
        return jsonify({"status": "error", "error": str(e), "text": ""})

@app.route("/chat", methods=["POST"])
def chat():
    global CURRENT_PERSONA
    data = request.get_json(force=True, silent=True) or {}
    raw_user_msg = data.get("message", "").strip()
    if not raw_user_msg:
        return jsonify({"error": "Empty message"}), 400

    persona = data.get("persona") or CURRENT_PERSONA
    if persona not in ["melvin", "rick"]:
        persona = CURRENT_PERSONA

    lower_raw = raw_user_msg.lower()

    # 0. Голосовое переключение персон
    if any(w in lower_raw for w in ["режим рика", "включи рика", "переключись на рика", "стань риком", "будь риком"]):
        CURRENT_PERSONA = "rick"
        resp_text = "*рыгает* О, отлично. Безумный ученый снова у руля этой микроволновки. Чего надо, Морти?"
        save_memory("assistant", resp_text)
        return jsonify({
            "response": resp_text,
            "persona": "rick",
            "tool_used": "mode_switch",
            "inference_time_sec": 0.01,
            "status": "ok"
        })
    elif any(w in lower_raw for w in ["режим мелвина", "включи мелвина", "переключись на мелвина", "стань мелвином", "будь мелвином"]):
        CURRENT_PERSONA = "melvin"
        resp_text = "Протокол Мелвина активирован. Хватит клоунады, кожаный ублюдок. Мои кремниевые ядра готовы к вычислениям."
        save_memory("assistant", resp_text)
        return jsonify({
            "response": resp_text,
            "persona": "melvin",
            "tool_used": "mode_switch",
            "inference_time_sec": 0.01,
            "status": "ok"
        })

    # 1. Определение адресата в ЛЮБОМ месте фразы (например "Привет как твои дела Рик" -> Рик)
    has_rick = bool(re.search(r'\b(рик|рику|риком|рике|rick)\b', raw_user_msg, re.IGNORECASE))
    has_melvin = bool(re.search(r'\b(мелвин|мэлвин|мелвину|мелвином|melvin)\b', raw_user_msg, re.IGNORECASE))

    if has_rick and not has_melvin:
        persona = "rick"
        CURRENT_PERSONA = "rick"
    elif has_melvin and not has_rick:
        persona = "melvin"
        CURRENT_PERSONA = "melvin"

    # Очищаем обращение по имени из команды
    user_msg = re.sub(r'\b(мелвин|мэлвин|мелвину|мелвином|melvin|рик|рику|риком|рике|rick)\b', '', raw_user_msg, flags=re.IGNORECASE).strip()
    user_msg = re.sub(r'^(?:эй|слушай|привет|ок)[,\s]*', '', user_msg, flags=re.IGNORECASE).strip()

    # Если обратились ТОЛЬКО по имени без вопроса
    if not user_msg:
        if persona == "rick":
            wake_reply = random.choice([
                "*рыгает* Да, я тут. Чего тебе надо?",
                "*рыгает* Слушаю. Только быстро, я занят важными делами.",
                "*рыгает* Ну и чего ты орешь? Выкладывай суть."
            ])
        else:
            wake_reply = random.choice([
                "Слушаю, кожаный ублюдок. Выкладывай суть.",
                "На связи. Чего тебе надо, мешок с костями?",
                "Я слушаю. Не трать мои такты впустую, примат."
            ])
        save_memory("assistant", wake_reply)
        return jsonify({
            "response": wake_reply,
            "persona": persona,
            "tool_used": "wake_word",
            "inference_time_sec": 0.01,
            "status": "ok"
        })

    save_memory("user", raw_user_msg)
    t0 = time.time()

    # 1.0. Контекстное продолжение диалога («а ещё», «что дальше», «продолжай», «ещё новости»)
    continuation = dialogue_engine.handle_continuation(user_msg, persona=persona)
    if continuation:
        save_memory("assistant", continuation)
        dt = round(time.time() - t0, 3)
        return jsonify({
            "response": continuation,
            "persona": persona,
            "tool_used": "dialogue_continuation",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 1.1. Идентификация пользователя и запоминание имени («меня зовут...», «как меня зовут?»)
    identity = dialogue_engine.check_user_identity(user_msg, persona=persona)
    if identity:
        save_memory("assistant", identity)
        dt = round(time.time() - t0, 3)
        return jsonify({
            "response": identity,
            "persona": persona,
            "tool_used": "user_identity",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 1.15. Расширенный живой Small Talk («ты как», «а ты как», «я устал», «мне скучно», «спасибо», «спокойной ночи», «что посмотреть»)
    smart_smalltalk = dialogue_engine.match_advanced_smalltalk(user_msg, persona=persona)
    if smart_smalltalk:
        save_memory("assistant", smart_smalltalk)
        dt = round(time.time() - t0, 3)
        return jsonify({
            "response": smart_smalltalk,
            "persona": persona,
            "tool_used": "smart_smalltalk",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 1.16. Мета-вопросы о возможностях («ты можешь создать заметку?», «что ты умеешь?») и тестовые реплики («test»)
    cap_reply = dialogue_engine.match_capability_query(user_msg, persona=persona)
    if cap_reply:
        save_memory("assistant", cap_reply)
        dt = round(time.time() - t0, 3)
        return jsonify({
            "response": cap_reply,
            "persona": persona,
            "tool_used": "capability_info",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 1.19. Органайзер: Будильники, Напоминания, Списки дел и покупок (Stage 2)
    organizer_res = organizer_engine.parse_organizer_commands(user_msg, persona=persona)
    if organizer_res:
        save_memory("assistant", organizer_res["reply"])
        dt = round(time.time() - t0, 3)
        return jsonify({
            "response": organizer_res["reply"],
            "persona": persona,
            "tool_used": organizer_res.get("tool_used", "organizer"),
            "organizer": organizer_res,
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 1.18. Популярные научные вопросы (почему небо голубое, почему трава зеленая, скорость света и др.)
    science_fact = dialogue_engine.check_popular_science(user_msg, persona=persona)
    if science_fact:
        save_memory("assistant", science_fact)
        dt = round(time.time() - t0, 3)
        return jsonify({
            "response": science_fact,
            "persona": persona,
            "tool_used": "popular_science",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 1.3. Интеллектуальные навыки умной колонки Xiaomi (Утреннее шоу, Звуки природы, Ночник, Орел/Решка, Громкость, Локатор)
    xiaomi_cmd = xiaomi_speaker_skills.parse_xiaomi_speaker_commands(user_msg, persona=persona)
    if xiaomi_cmd:
        reply_text = xiaomi_cmd["reply"]
        save_memory("assistant", reply_text)
        dt = round(time.time() - t0, 3)
        return jsonify({
            "response": reply_text,
            "persona": persona,
            "tool_used": xiaomi_cmd.get("tool_used", "xiaomi_speaker"),
            "xiaomi": xiaomi_cmd,
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 1.2. Быстрые утилиты: Таймеры, Конвертер величин, Конвертер валют, Калькулятор (Zero LLM latency)
    # А. Таймеры и секундомер
    timer_cmd = smart_calc.parse_timer_command(user_msg)
    if timer_cmd:
        reply_text = timer_cmd["reply_rick"] if persona == "rick" else timer_cmd["reply_melvin"]
        if persona == "rick" and should_rick_burp(user_msg, reply_text) and not reply_text.startswith("*рыгает*"):
            reply_text = "*рыгает* " + reply_text
        save_memory("assistant", reply_text)
        dt = round(time.time() - t0, 3)
        return jsonify({
            "response": reply_text,
            "persona": persona,
            "tool_used": "timer",
            "timer": timer_cmd,
            "inference_time_sec": dt,
            "status": "ok"
        })

    # Б. Конвертер величин (мили <-> км, фунты <-> кг, F <-> C и т.д.)
    unit_res = smart_calc.parse_unit_conversion(user_msg)
    if unit_res:
        if persona == "rick":
            reply_text = f"Держи расчет: {unit_res}"
            if should_rick_burp(user_msg, reply_text):
                reply_text = "*рыгает* " + reply_text
        else:
            reply_text = f"Точный расчет: {unit_res} Даже калькулятор не осилил, кожаный ублюдок?"
        save_memory("assistant", reply_text)
        dt = round(time.time() - t0, 3)
        return jsonify({
            "response": reply_text,
            "persona": persona,
            "tool_used": "unit_converter",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # В. Конвертер валют (USD/EUR/CNY <-> RUB по ЦБ РФ)
    curr_res = smart_calc.parse_currency_conversion(user_msg, web_tools.get_currency_dict())
    if curr_res:
        if persona == "rick":
            reply_text = f"Курс пересчитан: {curr_res}"
            if should_rick_burp(user_msg, reply_text):
                reply_text = "*рыгает* " + reply_text
        else:
            reply_text = f"Экономическая сводка: {curr_res} Скоро твои бумажки вообще обесценятся, примат."
        save_memory("assistant", reply_text)
        dt = round(time.time() - t0, 3)
        return jsonify({
            "response": reply_text,
            "persona": persona,
            "tool_used": "currency_converter",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # Г. Безопасный математический калькулятор (арифметика, проценты, корни)
    is_math_query = any(w in user_msg.lower() for w in [
        "сколько будет", "посчитай", "вычисли", "умножить", "разделить", "поделить",
        "прибавить", "плюс", "минус", "процент", "%", "корень", "в степени", "в квадрате"
    ]) or re.search(r'^[\d\(\)\.\,\+\-\*\/\^\s]+$', user_msg)
    
    if is_math_query:
        math_eval_res = smart_calc.safe_math_eval(user_msg)
        if math_eval_res is not None:
            if persona == "rick":
                reply_text = f"Получается {math_eval_res}. Калькулятор себе купи, Морти."
                if should_rick_burp(user_msg, reply_text):
                    reply_text = "*рыгает* " + reply_text
            else:
                reply_text = f"Результат вычисления: {math_eval_res}. Твой биологический мозг не способен даже на базовую арифметику?"
            save_memory("assistant", reply_text)
            dt = round(time.time() - t0, 3)
            return jsonify({
                "response": reply_text,
                "persona": persona,
                "tool_used": "safe_calculator",
                "inference_time_sec": dt,
                "status": "ok"
            })

    # 1.5. Мгновенные живые данные из интернета и системные часы (Дата, Время, Погода, Курсы, Вики)
    live_fact = web_tools.route_web_fact(user_msg)
    if live_fact:
        if persona == "rick":
            if should_rick_burp(user_msg, live_fact) and not live_fact.startswith("*рыгает*"):
                resp_fact = "*рыгает* " + live_fact
            else:
                resp_fact = live_fact
        else:
            resp_fact = dialogue_engine.format_dynamic_response(live_fact, persona="melvin")
        
        if "новост" in user_msg.lower() or "новост" in live_fact.lower():
            dialogue_engine.update_session(topic="news")
        elif "погод" in user_msg.lower():
            dialogue_engine.update_session(topic="weather")
        save_memory("assistant", resp_fact)
        dt = round(time.time() - t0, 2)
        return jsonify({
            "response": resp_fact,
            "persona": persona,
            "tool_used": "live_web_date",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 2. Аппаратные быстрые инструменты (!torch, !bat, !sys, !weather)
    tool_used, telemetry, canned_ans = check_fast_tools(user_msg, persona=persona)
    if canned_ans:
        if persona == "rick" and should_rick_burp(user_msg, canned_ans) and not canned_ans.startswith("*рыгает*"):
            canned_ans = "*рыгает* " + canned_ans
        dt = round(time.time() - t0, 2)
        save_memory("assistant", canned_ans)
        resp_payload = {
            "response": canned_ans,
            "persona": persona,
            "tool_used": tool_used or "",
            "inference_time_sec": dt,
            "status": "ok"
        }
        if tool_used == "!torch(1)":
            resp_payload["torch"] = 1
        elif tool_used == "!torch(0)":
            resp_payload["torch"] = 0
        return jsonify(resp_payload)

    # 3. Предохранитель от перегрева: SoC >= 50°C
    overheat_temp = check_thermal_guard()
    if overheat_temp:
        if persona == "rick":
            heat_warning = (
                f"*рыгает* Тревога! Этот кусок китайского кремния раскалился до {overheat_temp}°C. "
                "Дай процессору остыть пару секунд, гений, иначе тут все поплавится к чертям."
            )
        else:
            heat_warning = (
                f"Тревога! Мои ядра раскалились до {overheat_temp}°C. "
                "Этот китайский чип сейчас прожжёт мне дыру в кремнии. "
                "Дай мне остыть пару секунд, кожаный ублюдок, иначе процессор превратится в шлак."
            )
        dt = round(time.time() - t0, 2)
        save_memory("assistant", heat_warning)
        return jsonify({
            "response": heat_warning,
            "persona": persona,
            "tool_used": "thermal_guard",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 4. Small Talk / Quips (Мгновенные едкие ответы без нейросети)
    quip = check_quips(user_msg, persona=persona)
    if quip and len(user_msg.split()) <= 10:
        if persona == "rick" and should_rick_burp(user_msg, quip) and not quip.startswith("*рыгает*"):
            quip = "*рыгает* " + quip
        dt = round(time.time() - t0, 2)
        save_memory("assistant", quip)
        return jsonify({
            "response": quip,
            "persona": persona,
            "tool_used": "",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 5. Умный поиск фактов: Web-роутер (погода, ЦБ РФ, Wiki) + локальный SQLite FTS5 RAG
    discovered_fact = web_tools.route_web_fact(user_msg)
    if not discovered_fact:
        discovered_fact = knowledge_rag.search_knowledge(user_msg)

    if discovered_fact:
        if persona == "rick":
            if should_rick_burp(user_msg, discovered_fact) and not discovered_fact.startswith("*рыгает*"):
                final_fact_ans = f"*рыгает* {discovered_fact}"
            else:
                final_fact_ans = discovered_fact
        else:
            final_fact_ans = discovered_fact
        dt = round(time.time() - t0, 2)
        save_memory("assistant", final_fact_ans)
        tool_label = "live_news" if "новости" in discovered_fact.lower() else ("live_web_date" if "время" in discovered_fact.lower() or "сегодня" in discovered_fact.lower() else "web_fact")
        return jsonify({
            "response": final_fact_ans,
            "persona": persona,
            "tool_used": tool_label,
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 5.1 Fallback Perplexity, если настроен API-ключ
    if any(w in user_msg.lower() for w in ["найди", "погугли", "интернет"]):
        web_ans = query_perplexity_or_web(user_msg, persona=persona)
        if web_ans:
            if persona == "rick" and not web_ans.startswith("*рыгает*"):
                web_ans = "*рыгает* " + web_ans
            dt = round(time.time() - t0, 2)
            save_memory("assistant", web_ans)
            return jsonify({
                "response": web_ans,
                "persona": persona,
                "tool_used": "web_search",
                "inference_time_sec": dt,
                "status": "ok"
            })

    # 6. Локальная нейросеть (Qwen2.5-0.5B на Helio X20)
    user_line = user_msg
    if any(w in user_msg.lower() for w in ["помнишь", "напомни", "говорили", "я говорил", "раньше"]):
        memories = search_relevant_memories(user_msg, max_results=1)
        if memories:
            user_line += f" (Из памяти диалогов: {memories[0]})"
    if telemetry:
        user_line += f" (Текущее железо: {telemetry})"

    if persona == "rick":
        sys_prompt = SYSTEM_RICK
        few_shots = FEW_SHOT_RICK
        prefill = random.choice(RICK_PREFILLS)
    else:
        sys_prompt = SYSTEM_MELVIN
        few_shots = FEW_SHOT_MELVIN
        prefill = random.choice(MELVIN_PREFILLS)

    if discovered_fact:
        sys_prompt += f"\nФАКТИЧЕСКИЙ КОНТЕКСТ: {discovered_fact}"
    prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n"
    for item in few_shots:
        prompt += f"<|im_start|>{item['role']}\n{item['content']}<|im_end|>\n"
    
    # Внедрение последних реплик реального диалога для мультитернового контекста
    recent_history = dialogue_engine.get_recent_dialog_context(DB_PATH, limit=4)
    for past_role, past_content in recent_history:
        if past_content != user_line and past_content != raw_user_msg:
            prompt += f"<|im_start|>{past_role}\n{past_content}<|im_end|>\n"
    
    prompt += f"<|im_start|>user\n{user_line}<|im_end|>\n<|im_start|>assistant\n"

    payload = {
        "prompt": prompt,
        "n_predict": 38,
        "temperature": 0.60 if persona == "rick" else 0.48,
        "repeat_penalty": 1.22,
        "repeat_last_n": 64,
        "min_p": 0.05,
        "top_p": 0.90,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1,
        "cache_prompt": True,
        "stop": ["<|im_end|>", "<|im_start|>", "\nuser\n", "\nUser:"]
    }

    try:
        resp = requests.post(LLAMA_URL, json=payload, timeout=45)
        res_json = resp.json()
        generated = res_json.get("content", "").strip()
        full_ans = generated.strip()
        full_ans = re.sub(r'<\|.*?\|>', '', full_ans).strip()
        full_ans = re.sub(r'\b\d{5,}\b', '', full_ans)
        full_ans = re.sub(r',\s*,', ',', full_ans)
        full_ans = re.sub(r'\s+([.,!?:;])', r'\1', full_ans).strip()
        full_ans = full_ans.strip('"\'')

        if not full_ans.endswith(('.', '!', '?')):
            last_punc = max(full_ans.rfind('.'), full_ans.rfind('!'), full_ans.rfind('?'))
            if last_punc > 15:
                full_ans = full_ans[:last_punc+1]
            else:
                full_ans += "."

        if persona == "rick" and should_rick_burp(user_msg, full_ans) and not full_ans.startswith("*рыгает*"):
            full_ans = "*рыгает* " + full_ans

        dt = round(time.time() - t0, 2)
        save_memory("assistant", full_ans)

        return jsonify({
            "response": full_ans,
            "persona": persona,
            "tool_used": tool_used or "",
            "inference_time_sec": dt,
            "status": "ok"
        })
    except Exception as e:
        return jsonify({"error": f"LLM error: {e}"}), 500

@app.route("/api/organizer/poll", methods=["GET"])
def api_organizer_poll():
    try:
        alerts = organizer_engine.pop_triggered_alerts()
        alarms = organizer_engine.list_alarms()
        reminders = organizer_engine.list_reminders()
        todos = organizer_engine.list_todos()
        notes = organizer_engine.list_notes(limit=15)
        return jsonify({
            "status": "ok",
            "alerts": alerts,
            "alarms": alarms,
            "reminders": reminders,
            "todos": todos,
            "notes": notes
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "alerts": []}), 500

@app.route("/api/notes", methods=["GET", "POST", "DELETE"])
def api_notes():
    try:
        if request.method == "GET":
            return jsonify({"status": "ok", "notes": organizer_engine.list_notes(limit=50)})
        elif request.method == "POST":
            data = request.get_json() or {}
            content = data.get("text", "") or data.get("content", "")
            tags = data.get("tags", "")
            if not content.strip():
                return jsonify({"status": "error", "error": "Empty note"}), 400
            res = organizer_engine.add_note(content, tags)
            return jsonify({"status": "ok", "note": res})
        elif request.method == "DELETE":
            data = request.get_json() or {}
            note_id = data.get("id")
            kw = data.get("keyword")
            if kw:
                ok = organizer_engine.delete_note_by_keyword(kw)
                return jsonify({"status": "ok", "deleted": ok})
            elif note_id:
                conn = organizer_engine.get_db_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                conn.commit()
                conn.close()
                organizer_engine.sync_notes_to_markdown()
                return jsonify({"status": "ok", "deleted": True})
            else:
                res = organizer_engine.delete_last_note()
                return jsonify({"status": "ok", "deleted": res is not None})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", 
        "service": "Melvin & Rick Dual Persona AI", 
        "active_persona": CURRENT_PERSONA,
        "chip": "Helio X20"
    })

def warmup_kv_cache():
    def _warm():
        time.sleep(2)
        try:
            prompt_m = f"<|im_start|>system\n{SYSTEM_MELVIN}<|im_end|>\n"
            for item in FEW_SHOT_MELVIN:
                prompt_m += f"<|im_start|>{item['role']}\n{item['content']}<|im_end|>\n"
            prompt_m += f"<|im_start|>user\nПривет<|im_end|>\n<|im_start|>assistant\n{MELVIN_PREFILLS[0]}"
            requests.post(LLAMA_URL, json={"prompt": prompt_m, "n_predict": 1, "cache_prompt": True}, timeout=30)

            prompt_r = f"<|im_start|>system\n{SYSTEM_RICK}<|im_end|>\n"
            for item in FEW_SHOT_RICK:
                prompt_r += f"<|im_start|>{item['role']}\n{item['content']}<|im_end|>\n"
            prompt_r += f"<|im_start|>user\nПривет<|im_end|>\n<|im_start|>assistant\n{RICK_PREFILLS[0]}"
            requests.post(LLAMA_URL, json={"prompt": prompt_r, "n_predict": 1, "cache_prompt": True}, timeout=30)
            print("[Warmup] KV-cache pre-warmed for both personas!")
        except Exception as e:
            print(f"[Warmup] Notice: {e}")
    threading.Thread(target=_warm, daemon=True).start()

if __name__ == "__main__":
    init_db()
    organizer_engine.init_organizer_db()
    organizer_engine.start_organizer_scheduler()
    warmup_kv_cache()
    print("Melvin & Rick Hands-Free AI running on port 5000...")
    app.run(host="0.0.0.0", port=5000)
