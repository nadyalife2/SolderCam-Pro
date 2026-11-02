import re
import math
import html
import urllib.parse

# =========================================================================
# 1. МАТЕМАТИЧЕСКИЙ КАЛЬКУЛЯТОР (БЕЗОПАСНЫЙ AST ПАРСЕР)
# =========================================================================

def safe_math_eval(expr_str: str):
    """Безопасный парсер арифметических выражений через regex + математические функции."""
    s = expr_str.lower().strip()
    # Замена русских математических терминов на операторы
    s = s.replace("умножить на", "*").replace("умножь на", "*").replace("помножить на", "*")
    s = s.replace("разделить на", "/").replace("поделить на", "/").replace("раздели на", "/")
    s = s.replace("в степени", "**").replace("в степень", "**").replace("в кубе", "**3").replace("в квадрате", "**2")
    s = s.replace("плюс", "+").replace("прибавить", "+")
    s = s.replace("минус", "-").replace("отнять", "-").replace("вычесть", "-")
    s = s.replace("х", "*").replace("x", "*")
    
    # Корень из числа
    m_sqrt = re.search(r'(?:корень|квадратный корень)\s+(?:из\s+)?(\d+(?:[\.,]\d+)?)', s)
    if m_sqrt:
        val = float(m_sqrt.group(1).replace(",", "."))
        res = math.sqrt(val)
        return int(res) if res.is_integer() else round(res, 4)

    # Процент от числа: "15% от 45000" или "15 процентов от 45000"
    m_pct = re.search(r'(\d+(?:[\.,]\d+)?)\s*(?:%|процент(?:а|ов)?)\s+от\s+(\d+(?:[\.,]\d+)?)', s)
    if m_pct:
        pct = float(m_pct.group(1).replace(",", "."))
        base = float(m_pct.group(2).replace(",", "."))
        res = (pct * base) / 100.0
        return int(res) if res.is_integer() else round(res, 4)

    # Чистка для стандартных выражений
    clean = re.sub(r'[^0-9\+\-\*\/\.\(\)\^]', '', s.replace(",", ".").replace("^", "**"))
    if not clean or not re.search(r'\d', clean):
        return None

    # Защита от опасных конструкций
    if any(b in clean for b in ["__", "import", "open", "exec", "eval", "os", "sys"]):
        return None

    try:
        # Проверяем, что выражение содержит только допустимые математические символы
        if re.match(r'^[0-9\+\-\*\/\.\(\)\s]+$', clean):
            res = eval(clean, {"__builtins__": None, "math": math}, {})
            if isinstance(res, (int, float)):
                return int(res) if float(res).is_integer() else round(float(res), 4)
    except Exception:
        pass
    return None

# =========================================================================
# 2. КОНВЕРТЕР ВЕЛИЧИН (Длина, Вес, Температура, Скорость, Объем)
# =========================================================================

UNIT_CONVERSIONS = [
    # Длина
    (r'(\d+(?:[\.,]\d+)?)\s*(?:миль|мили|миля|милю)\s+(?:в|в\s+переводе\s+на)\s+(?:километр|км)',
     lambda v: (v * 1.60934, "км")),
    (r'(\d+(?:[\.,]\d+)?)\s*(?:километр|километра|километров|км)\s+(?:в|в\s+переводе\s+на)\s+(?:миль|мили|милю)',
     lambda v: (v / 1.60934, "миль")),
    (r'(\d+(?:[\.,]\d+)?)\s*(?:дюйм|дюйма|дюймов)\s+(?:в|в\s+переводе\s+на)\s+(?:сантиметр|см)',
     lambda v: (v * 2.54, "см")),
    (r'(\d+(?:[\.,]\d+)?)\s*(?:сантиметр|сантиметра|сантиметров|см)\s+(?:в|в\s+переводе\s+на)\s+(?:дюйм|дюйма|дюймов)',
     lambda v: (v / 2.54, "дюймов")),
    (r'(\d+(?:[\.,]\d+)?)\s*(?:фут|фута|футов)\s+(?:в|в\s+переводе\s+на)\s+(?:метр|метра|метров|м)',
     lambda v: (v * 0.3048, "м")),
    (r'(\d+(?:[\.,]\d+)?)\s*(?:метр|метра|метров|м)\s+(?:в|в\s+переводе\s+на)\s+(?:фут|фута|футов)',
     lambda v: (v / 0.3048, "футов")),

    # Вес
    (r'(\d+(?:[\.,]\d+)?)\s*(?:фунт|фунта|фунтов)\s+(?:в|в\s+переводе\s+на)\s+(?:килограмм|килограмма|килограммов|кг)',
     lambda v: (v * 0.453592, "кг")),
    (r'(\d+(?:[\.,]\d+)?)\s*(?:килограмм|килограмма|килограммов|кг)\s+(?:в|в\s+переводе\s+на)\s+(?:фунт|фунта|фунтов)',
     lambda v: (v / 0.453592, "фунтов")),
    (r'(\d+(?:[\.,]\d+)?)\s*(?:унций|унции|унция)\s+(?:в|в\s+переводе\s+на)\s+(?:грамм|грамма|граммов|г)',
     lambda v: (v * 28.3495, "г")),

    # Температура
    (r'(\d+(?:[\.,]\d+)?)\s*(?:фаренгейт|фаренгейта|градус(?:ов|а)?\s+фаренгейта)\s+(?:в|в\s+переводе\s+на)\s+(?:цельсий|цельсия|градус(?:ов|а)?\s+цельсия)',
     lambda v: ((v - 32.0) * 5.0 / 9.0, "°C")),
    (r'(\d+(?:[\.,]\d+)?)\s*(?:цельсий|цельсия|градус(?:ов|а)?\s+цельсия)\s+(?:в|в\s+переводе\s+на)\s+(?:фаренгейт|фаренгейта|градус(?:ов|а)?\s+фаренгейта)',
     lambda v: (v * 9.0 / 5.0 + 32.0, "°F")),

    # Скорость
    (r'(\d+(?:[\.,]\d+)?)\s*(?:узлов|узла|узел)\s+(?:в|в\s+переводе\s+на)\s+(?:км/ч|километр(?:ов)?\s+в\s+час)',
     lambda v: (v * 1.852, "км/ч")),
    (r'(\d+(?:[\.,]\d+)?)\s*(?:миль\s+в\s+час|mph)\s+(?:в|в\s+переводе\s+на)\s+(?:км/ч|километр(?:ов)?\s+в\s+час)',
     lambda v: (v * 1.60934, "км/ч"))
]

def parse_unit_conversion(text: str):
    s = text.lower().strip()
    for pattern, conv_fn in UNIT_CONVERSIONS:
        m = re.search(pattern, s)
        if m:
            val = float(m.group(1).replace(",", "."))
            res, unit = conv_fn(val)
            formatted = int(res) if res.is_integer() else round(res, 2)
            orig_val = int(val) if val.is_integer() else val
            return f"{orig_val} равно {formatted} {unit}."
    return None

# =========================================================================
# 3. КОНВЕРТЕР ВАЛЮТ ПО КУРСУ ЦБ РФ
# =========================================================================

def parse_currency_conversion(text: str, rates: dict):
    """
    Конвертирует валюты (USD, EUR, CNY) в RUB и наоборот.
    rates = {'usd': 96.5, 'eur': 105.2, 'cny': 13.5}
    """
    s = text.lower().strip()
    if not rates or not rates.get('usd'):
        return None

    # X долларов/евро/юаней в рублях
    m_to_rub = re.search(r'(\d+(?:[\.,]\d+)?)\s*(доллар(?:а|ов)?|usd|\$|евро|eur|€|юан(?:ей|я|ь)|cny)\s+(?:в|переведи\s+в)\s+рубл', s)
    if m_to_rub:
        val = float(m_to_rub.group(1).replace(",", "."))
        curr = m_to_rub.group(2)
        rate = rates.get('usd', 96.0)
        curr_name = "долларов"
        if any(k in curr for k in ["евро", "eur", "€"]):
            rate = rates.get('eur', 105.0)
            curr_name = "евро"
        elif any(k in curr for k in ["юан", "cny"]):
            rate = rates.get('cny', 13.5)
            curr_name = "юаней"
        
        rub_res = round(val * rate, 2)
        orig_val = int(val) if val.is_integer() else val
        return f"{orig_val} {curr_name} по курсу ЦБ РФ — это примерно {rub_res} рублей."

    # X рублей в долларах/евро/юанях
    m_from_rub = re.search(r'(\d+(?:[\.,]\d+)?)\s*(?:рубл(?:ей|я|ь)|руб)\s+(?:в|переведи\s+в)\s+(доллар|usd|\$|евро|eur|€|юан|cny)', s)
    if m_from_rub:
        val = float(m_from_rub.group(1).replace(",", "."))
        curr = m_from_rub.group(2)
        rate = rates.get('usd', 96.0)
        curr_name = "долларов"
        if any(k in curr for k in ["евро", "eur", "€"]):
            rate = rates.get('eur', 105.0)
            curr_name = "евро"
        elif any(k in curr for k in ["юан", "cny"]):
            rate = rates.get('cny', 13.5)
            curr_name = "юаней"
        
        res = round(val / rate, 2)
        orig_val = int(val) if val.is_integer() else val
        return f"{orig_val} рублей по курсу ЦБ РФ — это примерно {res} {curr_name}."

    return None

# =========================================================================
# 4. ТАЙМЕРЫ И СЕКУНДОМЕР
# =========================================================================

def parse_timer_command(text: str):
    """
    Распознает команды таймера:
    - "поставь таймер на 5 минут"
    - "таймер на 30 секунд"
    - "засеки 2 минуты"
    - "таймер на 1 час"
    - "отмени таймер" / "сбрось таймер"
    - "сколько осталось на таймере"
    """
    s = text.lower().strip()

    # Отмена таймера
    if any(k in s for k in ["отмени таймер", "сбрось таймер", "выключи таймер", "останови таймер", "удали таймер"]):
        return {
            "action": "cancel",
            "reply_rick": "Вырубил таймер. Занимайся чем хочешь, мне без разницы.",
            "reply_melvin": "Таймер аннулирован. Модуль отсчёта остановлен."
        }

    # Статус таймера
    if any(k in s for k in ["сколько осталось на таймере", "сколько на таймере", "статус таймера", "что с таймером"]):
        return {
            "action": "status",
            "reply_rick": "Таймер ещё тикает. Не дергай меня каждую секунду.",
            "reply_melvin": "Отсчёт времени продолжается согласно заданному интервалу."
        }

    # Распознавание времени
    is_timer = any(w in s for w in ["таймер", "засеки", "поставь на", "разбуди через", "напомни через"])
    if not is_timer:
        return None

    total_seconds = 0
    label_parts = []

    # Часы
    m_h = re.search(r'(\d+)\s*(?:час(?:а|ов)?|ч)\b', s)
    if m_h:
        h = int(m_h.group(1))
        total_seconds += h * 3600
        label_parts.append(f"{h} ч")
    elif "полтора часа" in s:
        total_seconds += 5400
        label_parts.append("1.5 ч")
    elif "полчаса" in s:
        total_seconds += 1800
        label_parts.append("30 мин")

    # Минуты
    m_m = re.search(r'(\d+)\s*(?:минут(?:ы|у)?|мин)\b', s)
    if m_m:
        m = int(m_m.group(1))
        total_seconds += m * 60
        label_parts.append(f"{m} мин")

    # Секунды
    m_s = re.search(r'(\d+)\s*(?:секунд(?:ы|у)?|сек)\b', s)
    if m_s:
        sec = int(m_s.group(1))
        total_seconds += sec
        label_parts.append(f"{sec} сек")

    # Просто число после таймера: "таймер 5" -> 5 минут
    if total_seconds == 0:
        m_num = re.search(r'(?:таймер|засеки)\s+(?:на\s+)?(\d+)\b', s)
        if m_num:
            m = int(m_num.group(1))
            total_seconds = m * 60
            label_parts.append(f"{m} мин")

    if total_seconds > 0:
        label = " ".join(label_parts)
        return {
            "action": "start",
            "duration_sec": total_seconds,
            "label": label,
            "reply_rick": f"Запустил таймер на {label}. Если не успеешь, сам будешь виноват.",
            "reply_melvin": f"Таймер на {label} активирован. Отсчёт времени запущен."
        }

    return None

# =========================================================================
# ТЕСТЫ
# =========================================================================
if __name__ == "__main__":
    print("256 * 16 =", safe_math_eval("сколько будет 256 умножить на 16"))
    print("15% от 45000 =", safe_math_eval("15% от 45000"))
    print("Корень из 144 =", safe_math_eval("корень из 144"))
    print("5 миль в км =", parse_unit_conversion("5 миль в километрах"))
    print("100 фаренгейта в цельсий =", parse_unit_conversion("100 фаренгейта в цельсиях"))
    print("Таймер 5 минут =", parse_timer_command("поставь таймер на 5 минут"))
    print("Таймер 30 секунд =", parse_timer_command("засеки 30 секунд"))
    print("Конвертер валют =", parse_currency_conversion("100 долларов в рублях", {"usd": 96.5, "eur": 105.0, "cny": 13.5}))
