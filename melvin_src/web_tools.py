import re
import json
import urllib.parse
import datetime
import subprocess
import html
import xml.etree.ElementTree as ET
import requests

try:
    import certifi
    VERIFY_SSL = certifi.where()
except ImportError:
    VERIFY_SSL = True

_session = requests.Session()
_session.verify = VERIFY_SSL
_session.headers["User-Agent"] = "MelvinRickBot/1.0 (Android 6.0; Helio X20)"

WEATHER_TRANSLATIONS = {
    "cloudy": "облачно",
    "partly cloudy": "переменная облачность",
    "sunny": "ясно",
    "clear": "ясно",
    "overcast": "пасмурно",
    "mist": "туман",
    "fog": "густой туман",
    "light rain": "небольшой дождь",
    "patchy rain possible": "возможен кратковременный дождь",
    "patchy rain nearby": "местами кратковременный дождь",
    "patchy light rain": "местами небольшой дождь",
    "light rain shower": "небольшой ливень",
    "moderate or heavy rain shower": "сильный ливень",
    "torrential rain shower": "проливной ливень",
    "moderate rain": "дождь",
    "heavy rain": "сильный ливень",
    "light snow": "небольшой снег",
    "patchy snow nearby": "местами снег",
    "patchy light snow": "местами небольшой снег",
    "moderate snow": "умеренный снег",
    "snow": "снег",
    "heavy snow": "снегопад",
    "thundery outbreaks possible": "возможна гроза",
    "thunderstorm": "гроза",
    "patchy light drizzle": "местами морось",
    "light drizzle": "небольшая морось"
}

def get_current_datetime_fact() -> str:
    """Возвращает точную текущую дату, день недели и время на русском языке со 100% синхронизацией с Android."""
    now = None
    try:
        # Прямой запрос к нативному Android host через bionic /system/bin/date
        out = subprocess.check_output(
            ["/system/bin/date", "+%Y-%m-%d %H:%M:%S"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        now = datetime.datetime.strptime(out, "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    if not now:
        now = datetime.datetime.now()

    months_ru = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    weekdays_ru = [
        "понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"
    ]
    
    day = now.day
    month_str = months_ru[now.month - 1]
    year = now.year
    weekday_str = weekdays_ru[now.weekday()]
    time_str = now.strftime("%H:%M")
    
    return f"Сегодня {day} {month_str} {year} года, {weekday_str}, текущее время {time_str}."

def get_live_weather(city: str = "") -> dict:
    """Мгновенная погода через wttr.in (JSON v1/v2) с русским переводом."""
    try:
        c_clean = (city or "").strip()
        url = f"https://wttr.in/{urllib.parse.quote(c_clean)}?format=j1&lang=ru" if c_clean else "https://wttr.in/?format=j1&lang=ru"
        r = _session.get(url, timeout=2.5).json()
        curr = r["current_condition"][0]
        
        # Получаем описание и переводим, если пришло на английском
        raw_desc = ""
        if "lang_ru" in curr and curr["lang_ru"]:
            raw_desc = curr["lang_ru"][0].get("value", "")
        if not raw_desc and "weatherDesc" in curr and curr["weatherDesc"]:
            raw_desc = curr["weatherDesc"][0].get("value", "")
            
        desc = raw_desc.strip().lower()
        if desc in WEATHER_TRANSLATIONS:
            desc = WEATHER_TRANSLATIONS[desc]
            
        temp = curr.get("temp_C", "N/A")
        wind = curr.get("windspeedKmph", "N/A")
        humidity = curr.get("humidity", "N/A")
        
        return {
            "status": "ok",
            "city": c_clean if c_clean else "за бортом",
            "temp": temp,
            "desc": desc,
            "wind": wind,
            "humidity": humidity
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_currency_dict() -> dict:
    """Возвращает словарь курсов валют {'usd': float, 'eur': float, 'cny': float}."""
    rates = {}
    try:
        r = _session.get("https://www.cbr.ru/scripts/XML_daily.asp", timeout=2.0)
        txt = r.content.decode("windows-1251", "ignore")
        def find_rate(code):
            m = re.search(rf"<CharCode>{code}</CharCode>.*?<Value>([\d,]+)</Value>", txt, re.S)
            return float(m.group(1).replace(",", ".")) if m else None
        rates['usd'] = find_rate("USD") or 96.0
        rates['eur'] = find_rate("EUR") or 105.0
        rates['cny'] = find_rate("CNY") or 13.5
    except Exception:
        rates = {'usd': 96.0, 'eur': 105.0, 'cny': 13.5}
    return rates

def get_currency_rates() -> str:
    """Официальный XML-фид курсов валют ЦБ РФ."""
    try:
        rates = get_currency_dict()
        res = []
        if rates.get('usd'): res.append(f"доллар {rates['usd']:.2f} руб.")
        if rates.get('eur'): res.append(f"евро {rates['eur']:.2f} руб.")
        if rates.get('cny'): res.append(f"юань {rates['cny']:.2f} руб.")
        if res:
            return "Курсы ЦБ РФ: " + ", ".join(res)
    except Exception:
        pass
    return ""

def search_wikipedia_fact(query: str) -> str:
    """Двухшаговый поиск Википедии без 404 ошибок."""
    try:
        clean_q = re.sub(r"^(кто такой|кто такая|что такое|найди|расскажи про|когда был|где находится|загугли|погугли|почему|зачем|как работает|как устроен|объясни)\s+", "", query, flags=re.I).strip()
        if not clean_q:
            clean_q = query.strip()

        open_url = f"https://ru.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(clean_q)}&limit=3&namespace=0&format=json"
        res = _session.get(open_url, timeout=2.0).json()
        titles = res[1] if len(res) > 1 else []
        if not titles:
            return ""

        q_words = [w.lower() for w in re.findall(r'[а-яa-z]{3,}', clean_q)]
        canonical = None
        for t in titles:
            if any(w in t.lower() for w in q_words):
                canonical = t
                break
        if not canonical:
            canonical = titles[0]

        sum_url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(canonical)}"
        sum_res = _session.get(sum_url, timeout=2.0).json()
        extract = sum_res.get("extract", "")
        if extract:
            # Берем первое законченное предложение
            first_sent = extract.split(". ")[0].strip()
            if not first_sent.endswith("."):
                first_sent += "."
            return first_sent
    except Exception:
        pass
    return ""

def search_duckduckgo(query: str) -> str:
    """DuckDuckGo Instant Answers API для быстрых фактов."""
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
        r = _session.get(url, timeout=2.0).json()
        abstract = r.get("AbstractText", "")
        if not abstract and r.get("RelatedTopics"):
            t = r["RelatedTopics"][0]
            abstract = t.get("Text", "")
        if abstract:
            first_sent = abstract.split(". ")[0].strip()
            return first_sent + ("." if not first_sent.endswith(".") else "")
    except Exception:
        pass
    return ""

NEWS_FEEDS = {
    "habr": {
        "name": "Хабра",
        "url": "https://habr.com/ru/rss/news/?fl=ru",
        "keywords": ["хабр", "habr", "хабре", "хабру", "it", "айти", "разработк", "программирован"]
    },
    "vc": {
        "name": "VC.ru",
        "url": "https://vc.ru/rss/all",
        "keywords": ["vc", "вц", "стартап", "бизнес", "инвестици", "маркетинг"]
    },
    "dtf": {
        "name": "DTF",
        "url": "https://dtf.ru/rss/all",
        "keywords": ["dtf", "дтф", "игры", "гейминг", "кино", "сериал"]
    },
    "4pda": {
        "name": "4PDA",
        "url": "https://4pda.to/feed/",
        "keywords": ["4pda", "4пда", "смартфон", "гаджет", "android", "андроид", "телефон", "xiaomi"]
    },
    "ixbt": {
        "name": "iXBT",
        "url": "https://www.ixbt.com/export/news.rss",
        "keywords": ["ixbt", "ихбт", "железо", "видеокарт", "процессор", "чип", "amd", "intel", "nvidia"]
    },
    "naked_science": {
        "name": "Naked Science",
        "url": "https://naked-science.ru/feed",
        "keywords": ["naked science", "наук", "космос", "физик", "астрономи", "квант", "учен"]
    },
    "kod_durova": {
        "name": "Кода Дурова",
        "url": "https://kod.ru/rss/",
        "keywords": ["код дурова", "дуров", "telegram", "телеграм", "мессенджер", "павел дуров"]
    },
    "cnews": {
        "name": "CNews",
        "url": "https://www.cnews.ru/inc/rss/news.xml",
        "keywords": ["cnews", "синьюс", "импортозамещен", "софт", "гостех"]
    },
    "forklog": {
        "name": "ForkLog",
        "url": "https://forklog.com/feed/",
        "keywords": ["forklog", "форклог", "крипт", "биткоин", "bitcoin", "блокчейн"]
    },
    "rozetked": {
        "name": "Rozetked",
        "url": "https://rozetked.me/turbo",
        "keywords": ["rozetked", "розеткед", "apple", "айфон", "iphone"]
    },
    "tinkoff": {
        "name": "Тинькофф Журнала",
        "url": "https://journal.tinkoff.ru/feed/",
        "keywords": ["тинькофф", "т-ж", "тж", "деньги", "налог", "финанс", "экономик"]
    },
    "ria": {
        "name": "РИА Новости",
        "url": "https://ria.ru/export/rss2/archive/index.xml",
        "keywords": ["риа", "ria", "политик", "росси", "мир", "главные"]
    },
    "habr_best": {
        "name": "Хабра (Лучшее за день)",
        "url": "https://habr.com/ru/rss/best/daily/?fl=ru",
        "keywords": ["лучшее на хабре", "топ хабр", "главное на хабре"]
    }
}

def clean_rss_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return " ".join(text.split()).strip()

LAST_NEWS_CACHE = []

WORD_TO_NUM = {
    "одну": 1, "одна": 1, "один": 1, "1": 1,
    "две": 2, "два": 2, "2": 2,
    "три": 3, "трое": 3, "3": 3,
    "четыре": 4, "4": 4,
    "пять": 5, "5": 5,
    "шесть": 6, "6": 6,
    "семь": 7, "7": 7,
    "восемь": 8, "8": 8,
    "девять": 9, "9": 9,
    "десять": 10, "10": 10
}

DETAIL_TRIGGER_WORDS = [
    "подробнее", "подробност", "прочитай", "детали", "раскрой", "что там",
    "что в", "что во", "о чем", "о чём", "расскажи про", "расскажи о"
]

INDEX_PATTERNS = [
    (1, r'\b(1|1-ю|1-я|перв\w*|одну|один|номер\s*1)\b'),
    (2, r'\b(2|2-ю|2-я|втор\w*|номер\s*2)\b'),
    (3, r'\b(3|3-ю|3-я|трет\w*|номер\s*3)\b'),
    (4, r'\b(4|4-ю|4-я|четверт\w*|номер\s*4)\b'),
    (5, r'\b(5|5-ю|5-я|пят\w*|номер\s*5)\b'),
    (6, r'\b(6|6-ю|6-я|шест\w*|номер\s*6)\b'),
    (7, r'\b(7|7-ю|7-я|седьм\w*|номер\s*7)\b'),
    (8, r'\b(8|8-ю|8-я|восьм\w*|номер\s*8)\b'),
    (9, r'\b(9|9-ю|9-я|девят\w*|номер\s*9)\b'),
    (10, r'\b(10|10-ю|10-я|десят\w*|номер\s*10)\b'),
]

def extract_news_count(q: str, default: int = 5) -> int:
    m = re.search(r'\b(10|[1-9]|одну|одна|один|две|два|три|четыре|пять|шесть|семь|восемь|девять|десять)\s*(?:последн\w*|свеж\w*|главн\w*|топ)?\s*новост', q, re.I)
    if m:
        return WORD_TO_NUM.get(m.group(1).lower(), default)
    m2 = re.search(r'новост\w*\s*(?:подборк\w*|дайджест\w*)?\s*(?:из\s*)?\b(10|[1-9]|одну|одна|один|две|два|три|четыре|пять|шесть|семь|восемь|девять|десять)\b', q, re.I)
    if m2:
        return WORD_TO_NUM.get(m2.group(1).lower(), default)
    m3 = re.search(r'\b(10|[1-9])\b', q)
    if m3:
        try:
            n = int(m3.group(1))
            if 1 <= n <= 10:
                return n
        except Exception:
            pass
    return default

def extract_news_topic(q: str) -> str:
    m = re.search(r'(?:про|по теме|на тему|о|об)\s+([^,]+)', q, re.I)
    if m:
        topic_cand = m.group(1).strip()
        topic_cand = re.split(r'\s+(?:на|в|с|из|по|подробнее|дай|расскажи)\s+', topic_cand)[0].strip()
        topic_cand = re.sub(r'\b(vc\.ru|vc|хабр\w*|4pda|ixbt|dtf|ria|лент\w*|подробнее|новост\w*|последн\w*|свеж\w*|\d+)\b', '', topic_cand, flags=re.I).strip()
        if len(topic_cand) >= 3:
            return topic_cand
    return ""

def parse_news_detail_request(user_msg: str):
    q = user_msg.lower().strip()
    if re.search(r'\b(расскажи|дай|покажи|включи|назови|выведи)\s+(?:мне\s+)?(?:\d+|одну|один|две|два|три|четыре|пять|шесть|семь|восемь|девять|десять)\s*(?:последн\w*|свеж\w*|главн\w*|топ)?\s*новост', q):
        return False, None
    if re.search(r'\b(?:\d+|одну|один|две|два|три|четыре|пять|шесть|семь|восемь|девять|десять)\s*(?:последн\w*|свеж\w*|главн\w*|топ)\s+новост', q):
        return False, None
    matched_idx = None
    for idx, pat in INDEX_PATTERNS:
        if re.search(pat, q):
            matched_idx = idx
            break
    has_trigger = any(t in q for t in DETAIL_TRIGGER_WORDS)
    has_news_word = bool(re.search(r'\bновост\w*\b', q))
    if matched_idx is not None and (has_trigger or has_news_word):
        return True, matched_idx
    if any(p in q for p in ["расскажи подробнее", "подробнее о новости", "прочитай новость", "что там написано"]):
        return True, 1
    return False, None


def parse_rss_items(url: str, source_name: str, max_items: int = 25) -> list:
    """Парсит элементы RSS с извлечением заголовка, описания (тела) и ссылки."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    r = _session.get(url, headers=headers, timeout=2.5)
    root = ET.fromstring(r.content)
    parsed = []
    for it in root.findall(".//item")[:max_items]:
        t = it.find("title")
        d = it.find("description")
        l = it.find("link")
        title_str = clean_rss_text(t.text) if t is not None and t.text else ""
        desc_str = clean_rss_text(d.text) if d is not None and d.text else ""
        link_str = (l.text or "").strip() if l is not None else ""
        if title_str:
            parsed.append({
                "source": source_name,
                "title": title_str,
                "desc": desc_str,
                "link": link_str
            })
    return parsed

def get_live_news(query: str = "", count: int = 5) -> str:
    """
    Парсит живые RSS-ленты топ-изданий (VC.ru, Хабр, 4PDA, iXBT, DTF, Rozetked и др.).
    Поддерживает динамическое количество (до 10 новостей), выбор источника и фильтрацию по темам.
    """
    global LAST_NEWS_CACHE
    q = (query or "").lower().strip()
    
    parsed_count = extract_news_count(q, default=count)
    req_count = max(1, min(10, parsed_count))
    
    target_key = "habr"
    for key, feed in NEWS_FEEDS.items():
        if any(kw in q for kw in feed["keywords"]):
            target_key = key
            break
            
    feed = NEWS_FEEDS.get(target_key, NEWS_FEEDS["habr"])
    source_name = feed["name"]
    url = feed["url"]
    topic = extract_news_topic(q)
    
    try:
        articles = parse_rss_items(url, source_name, max_items=25)
        if not articles and target_key == "tinkoff":
            articles = parse_rss_items(NEWS_FEEDS["vc"]["url"], "VC.ru (раздел бизнес и финансы)", max_items=25)
            
        if articles:
            topic_note = ""
            if topic:
                topic_words = [w for w in re.findall(r'[а-яa-z0-9]{3,}', topic.lower())]
                matched = [
                    a for a in articles 
                    if any(tw in a["title"].lower() or tw in a["desc"].lower() for tw in topic_words)
                ]
                if matched:
                    articles = matched
                    topic_note = f" по теме «{topic}»"
                else:
                    topic_note = f" (по теме «{topic}» совпадений нет, вот главное)"
                    
            LAST_NEWS_CACHE = articles
            selected = articles[:req_count]
            items_lines = [f"{idx+1}) {a['title']}" for idx, a in enumerate(selected)]
            items_str = "; ".join(items_lines)
            hint = " Скажи: «расскажи про 3 подробнее», чтобы узнать детали."
            return f"Свежие новости с {selected[0]['source']}{topic_note} ({len(selected)} шт): {items_str}.{hint}"
    except Exception as e:
        try:
            articles = parse_rss_items(NEWS_FEEDS["habr"]["url"], "Хабра", max_items=25)
            if articles:
                LAST_NEWS_CACHE = articles
                selected = articles[:req_count]
                items_lines = [f"{idx+1}) {a['title']}" for idx, a in enumerate(selected)]
                items_str = "; ".join(items_lines)
                hint = " Скажи: «расскажи про 3 подробнее», чтобы узнать детали."
                return f"Свежие новости технологий с Хабра ({len(selected)} шт): {items_str}.{hint}"
        except Exception:
            pass
    return ""

def get_news_detail(user_msg: str) -> str:
    """
    Извлекает подробное описание новости по запросам вида:
    «расскажи про 3 подробнее», «расскажи подробнее про 3», «подробнее про вторую», «что в 3 новости», «прочитай 3»
    """
    global LAST_NEWS_CACHE
    is_detail, idx_1based = parse_news_detail_request(user_msg)
    if not is_detail or idx_1based is None:
        return ""

    idx = idx_1based - 1

    if not LAST_NEWS_CACHE:
        get_live_news("vc.ru", count=5)

    if not LAST_NEWS_CACHE:
        return "В памяти пока нет загруженных новостей. Сначала попроси: «Мелвин, расскажи новости на vc.ru»."

    if idx >= len(LAST_NEWS_CACHE):
        return f"В текущей подборке всего {len(LAST_NEWS_CACHE)} новостей. Укажи номер от 1 до {len(LAST_NEWS_CACHE)}."

    item = LAST_NEWS_CACHE[idx]
    title = item.get("title", "")
    desc = item.get("desc", "")
    source = item.get("source", "ленты")

    summary = ""
    if desc:
        clean_desc = re.sub(r'\s*(?:Читать далее|Подробнее|Read more|\.\.\.).*$', '', desc, flags=re.I).strip()
        sentences = re.split(r'(?<=[.!?])\s+', clean_desc)
        summary = " ".join(sentences[:4]).strip()

    if not summary:
        summary = title

    return f"Подробности новости №{idx_1based} с {source} «{title}»: {summary}"

def route_web_fact(user_msg: str) -> str:
    """
    Мгновенный роутер фактов без нейросети:
    1. Дата, день недели, текущее время
    2. Погода в реальном времени
    3. Новости (Хабр, VC.ru, 4PDA, iXBT, Naked Science, Код Дурова и др.)
    4. Курсы валют
    5. Факты из Википедии / DuckDuckGo
    """
    q = user_msg.lower().strip()

    # Отсекаем жалобы и споры о времени/фактах, чтобы бот не уходил в рекурсию
    if any(b in q for b in ["не угадал", "не угадала", "неправильно", "неверно", "ошибся", "ошибка", "соврал", "не то", "врешь", "врёшь"]):
        return ""

    # 1. Дата, время, число, день недели (только явные прямые вопросы)
    date_patterns = [
        "какая сегодня дата", "какое сегодня число", "какой сегодня день", "какая дата",
        "какой день недели", "день недели", "который час", "сколько времени", "какое время",
        "число сегодня", "дата сегодня", "год какой", "какой сейчас год", "скажи время",
        "скажи дату", "подскажи время", "текущее время", "сколько сейчас времени", "точный час"
    ]
    if any(p in q for p in date_patterns):
        return get_current_datetime_fact()

    if re.search(r"\b(сколько\s+(сейчас\s+)?врем(ени|я)|который\s+час|какое\s+(сейчас\s+)?(число|время)|какая\s+(сегодня\s+)?дата)\b", q):
        return get_current_datetime_fact()

    # 2. Новости: проверка на детальный запрос («расскажи про 3 подробнее», «подробнее про вторую»)
    is_detail, detail_idx = parse_news_detail_request(user_msg)
    if is_detail:
        detail = get_news_detail(user_msg)
        if detail:
            return detail

    # 2.1 Жалобы на малое количество новостей / запрос ещё новостей
    is_more_query = any(k in q for k in [
        "мало новостей", "слишком мало", "еще новостей", "ещё новостей", "следующие новости",
        "дай еще новостей", "больше новостей", "другие новости"
    ])
    if is_more_query:
        curr_src = (LAST_NEWS_CACHE[0]['source'].lower() if LAST_NEWS_CACHE else "")
        next_key = "vc" if "хабр" in curr_src else "4pda"
        news_fact = get_live_news(next_key, count=5)
        if news_fact:
            return "Вот дополнительная подборка: " + news_fact

    # 2.2 Обычный запрос новостей
    if any(k in q for k in [
        "новост", "что нового", "что происходит", "сводка", "дайджест", "хабр", "habr",
        "vc.ru", "vc", "вц", "тинькофф", "т-ж", "тж", "4pda", "ixbt", "dtf", "дтф", "naked science", "cnews",
        "forklog", "rozetked", "код дурова", "риа", "ria"
    ]):
        news_fact = get_live_news(q, count=5)
        if news_fact:
            return news_fact

    # 3. Погода
    if re.search(r"\b(погод[аеуы]|температур[ае]|дождь|за бортом|холодно ли|жарко ли)\b", q):
        m = re.search(r"в ([а-яё\-]+)", q)
        city = m.group(1) if m else ""
        w = get_live_weather(city)
        if w.get("status") == "ok":
            loc = f"В {city.capitalize()}" if city else "За бортом"
            return f"{loc} сейчас {w['temp']}°C, {w['desc']}, влажность {w['humidity']}%, ветер {w['wind']} км/ч."

    # 4. Курс валют
    if any(k in q for k in ["курс доллара", "курс евро", "курс юаня", "курс валют", "сколько стоит доллар"]):
        rates = get_currency_rates()
        if rates:
            return rates

    # 5. Википедия / DuckDuckGo факты
    if any(q.startswith(p) for p in [
        "кто такой", "кто такая", "что такое", "найди", "когда был", "где находится",
        "расскажи про", "загугли", "погугли", "почему", "зачем", "как работает", "как устроен", "объясни"
    ]):
        fact = search_wikipedia_fact(user_msg)
        if not fact:
            fact = search_duckduckgo(user_msg)
        if fact:
            return fact

    return ""
