"""
Melvin & Rick Smart Organizer Engine:
1. Alarms (Будильники):
   - Установка: "поставь будильник на 7:30", "разбуди в 8:00", "будильник на 9 утра"
   - Управление: "список будильников", "выключи будильник", "удали все будильники"
2. Reminders (Напоминания):
   - По времени: "напомни купить молоко в 18:00", "напомни завтра в 10:00 совещание"
   - По таймеру: "напомни через 45 минут выключить духовку", "напомни через 2 часа забрать заказ"
   - Просмотр и удаление: "какие напоминания", "удали напоминание про молоко"
3. To-Do & Shopping Lists (Списки дел и покупок):
   - Добавление: "добавь в список покупок хлеб, сыр и яблоки", "запиши в список дел починить кран"
   - Просмотр: "что в списке покупок", "прочитай список дел"
   - Завершение/удаление: "вычеркни сыр", "удали из списка покупок хлеб", "очисти список дел"
"""

import os
import re
import time
import datetime
import sqlite3
import random
import threading

DB_PATH = "/melvin/data/agent_memory.db"
if not os.path.exists(os.path.dirname(DB_PATH)):
    DB_PATH = "agent_memory.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.create_function("ru_lower", 1, lambda s: (s or "").lower())
    return conn

# Очередь сработавших алертов (будильники, напоминания), готовых к воспроизведению
TRIGGERED_ALERTS = []

def init_organizer_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_str TEXT NOT NULL,
            hour INTEGER NOT NULL,
            minute INTEGER NOT NULL,
            label TEXT DEFAULT 'Будильник',
            is_active INTEGER DEFAULT 1,
            days TEXT DEFAULT 'everyday',
            created_at REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remind_time_str TEXT,
            target_timestamp REAL NOT NULL,
            text TEXT NOT NULL,
            is_done INTEGER DEFAULT 0,
            created_at REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT DEFAULT 'tasks',
            item_text TEXT NOT NULL,
            is_completed INTEGER DEFAULT 0,
            created_at REAL
        )
    """)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            content TEXT,
            tags TEXT
        )
    ''')
    conn.commit()
    conn.close()

# =========================================================================
# 1. БУДИЛЬНИКИ (ALARMS)
# =========================================================================

def parse_time_hh_mm(text: str):
    """Извлекает часы и минуты из текста: 7:30, 07:30, 8 утра, 9 вечера, 19:45."""
    s = text.lower().strip()
    
    # 7:30 или 07:30 или 7.30
    m_col = re.search(r'\b([01]?\d|2[0-3])[:\.\s]([0-5]\d)\b', s)
    if m_col:
        h = int(m_col.group(1))
        m = int(m_col.group(2))
        return h, m

    # 8 утра / 8 вечера
    m_single = re.search(r'\b([01]?\d|2[0-3])\s*(?:час(?:а|ов)?)?\s*(утра|вечера|дня|ночи)?\b', s)
    if m_single:
        h = int(m_single.group(1))
        period = m_single.group(2)
        if period in ["вечера", "дня"] and h < 12:
            h += 12
        elif period in ["ночи", "утра"] and h == 12:
            h = 0
        return h, 0

    return None, None

def set_alarm(hour: int, minute: int, label: str = "Будильник") -> dict:
    time_str = f"{hour:02d}:{minute:02d}"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Деактивируем дубликат, если уже есть на то же время
    cur.execute("DELETE FROM alarms WHERE time_str = ?", (time_str,))
    cur.execute("INSERT INTO alarms (time_str, hour, minute, label, is_active, created_at) VALUES (?, ?, ?, ?, 1, ?)",
                (time_str, hour, minute, label, time.time()))
    conn.commit()
    conn.close()
    return {"status": "ok", "time_str": time_str, "hour": hour, "minute": minute}

def list_alarms() -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, time_str, label, is_active FROM alarms ORDER BY hour, minute")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "time_str": r[1], "label": r[2], "active": bool(r[3])} for r in rows]

def clear_all_alarms():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM alarms")
    conn.commit()
    conn.close()

def delete_alarm_by_time(hour: int, minute: int):
    time_str = f"{hour:02d}:{minute:02d}"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM alarms WHERE time_str = ?", (time_str,))
    rows = cur.rowcount
    conn.commit()
    conn.close()
    return rows > 0

# =========================================================================
# 2. НАПОМИНАНИЯ (REMINDERS)
# =========================================================================

def set_reminder_relative(seconds: int, text: str) -> dict:
    target_ts = time.time() + seconds
    dt = datetime.datetime.fromtimestamp(target_ts)
    time_str = dt.strftime("%H:%M")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO reminders (remind_time_str, target_timestamp, text, is_done, created_at) VALUES (?, ?, ?, 0, ?)",
                (time_str, target_ts, text, time.time()))
    conn.commit()
    conn.close()
    return {"status": "ok", "time_str": time_str, "text": text, "target_ts": target_ts}

def set_reminder_absolute(hour: int, minute: int, text: str) -> dict:
    now = datetime.datetime.now()
    target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target_dt <= now:
        target_dt += datetime.timedelta(days=1)
    target_ts = target_dt.timestamp()
    time_str = f"{hour:02d}:{minute:02d}"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO reminders (remind_time_str, target_timestamp, text, is_done, created_at) VALUES (?, ?, ?, 0, ?)",
                (time_str, target_ts, text, time.time()))
    conn.commit()
    conn.close()
    return {"status": "ok", "time_str": time_str, "text": text, "target_ts": target_ts}

def list_reminders(only_pending: bool = True) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    query = "SELECT id, remind_time_str, text, is_done FROM reminders"
    if only_pending:
        query += " WHERE is_done = 0"
    query += " ORDER BY target_timestamp ASC LIMIT 10"
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "time": r[1], "text": r[2], "done": bool(r[3])} for r in rows]

def clear_all_reminders():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders")
    conn.commit()
    conn.close()

# =========================================================================
# 3. СПИСОК ДЕЛ И ПОКУПОК (TO-DO & SHOPPING LIST)
# =========================================================================

def add_todos(items: list, category: str = "tasks"):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    added = []
    for it in items:
        clean = it.strip().capitalize()
        if clean:
            cur.execute("INSERT INTO todos (category, item_text, is_completed, created_at) VALUES (?, ?, 0, ?)",
                        (category, clean, time.time()))
            added.append(clean)
    conn.commit()
    conn.close()
    return added

def list_todos(category: str = None) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if category:
        cur.execute("SELECT id, category, item_text, is_completed FROM todos WHERE category = ? AND is_completed = 0 ORDER BY id DESC", (category,))
    else:
        cur.execute("SELECT id, category, item_text, is_completed FROM todos WHERE is_completed = 0 ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "cat": r[1], "text": r[2], "done": bool(r[3])} for r in rows]

def complete_todo_item(item_keyword: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    conn.create_function("ru_lower", 1, lambda s: (s or "").lower())
    cur = conn.cursor()
    kw = f"%{item_keyword.lower().strip()}%"
    cur.execute("UPDATE todos SET is_completed = 1 WHERE ru_lower(item_text) LIKE ? AND is_completed = 0", (kw,))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def clear_todos(category: str = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if category:
        cur.execute("DELETE FROM todos WHERE category = ?", (category,))
    else:
        cur.execute("DELETE FROM todos")
    conn.commit()
    conn.close()

# =========================================================================
# 4. ОБРАБОТЧИК ГОЛОСОВЫХ КОМАНД (NATURAL LANGUAGE ROUTER)
# =========================================================================


NOTES_MD_PATH = "/melvin/notes.md"
if not os.path.exists(os.path.dirname(NOTES_MD_PATH)):
    NOTES_MD_PATH = "/sdcard/melvin/notes.md"
if not os.path.exists(os.path.dirname(NOTES_MD_PATH)):
    NOTES_MD_PATH = "notes.md"

def sync_notes_to_markdown():
    """Синхронизирует все активные заметки в человекочитаемый Markdown-файл."""
    try:
        notes = list_notes(limit=200)
        target_path = NOTES_MD_PATH
        d = os.path.dirname(target_path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        lines = [
            "# 📓 Melvin & Rick Voice Notes Archive",
            f"*Синхронизировано: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}*",
            "",
        ]
        if not notes:
            lines.append("*(Архив заметок пуст)*")
        else:
            for n in reversed(notes): # Хронологический порядок
                tag_part = f" `[{n['tags']}]`" if n.get("tags") else ""
                lines.append(f"- **{n['created_at']}**{tag_part}: {n['content']}")
        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        print(f"[Notes Markdown Sync Error]: {e}")

def add_note(content: str, tags: str = "") -> dict:
    """Добавляет новую голосовую заметку/мысль в SQLite и обновляет notes.md."""
    conn = get_db_connection()
    cur = conn.cursor()
    now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    clean_text = content.strip()
    if clean_text:
        clean_text = clean_text[0].upper() + clean_text[1:]
    cur.execute("INSERT INTO notes (created_at, content, tags) VALUES (?, ?, ?)",
                (now_str, clean_text, tags))
    note_id = cur.lastrowid
    conn.commit()
    conn.close()
    sync_notes_to_markdown()
    return {"id": note_id, "created_at": now_str, "content": clean_text, "tags": tags}

def list_notes(limit: int = 20) -> list:
    """Возвращает последние заметки."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, created_at, content, tags FROM notes ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "created_at": r[1], "content": r[2], "tags": r[3] or ""} for r in rows]

def get_last_note() -> dict:
    """Возвращает самую свежую заметку."""
    notes = list_notes(limit=1)
    return notes[0] if notes else None

def search_notes(keyword: str) -> list:
    """Ищет заметки по ключевому слову независимо от регистра."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, created_at, content, tags FROM notes WHERE ru_lower(content) LIKE ? ORDER BY id DESC LIMIT 10",
                (f"%{keyword.lower()}%",))
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "created_at": r[1], "content": r[2], "tags": r[3] or ""} for r in rows]

def delete_last_note() -> dict:
    """Удаляет последнюю добавленную заметку."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, created_at, content, tags FROM notes ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    del_note = {"id": row[0], "created_at": row[1], "content": row[2], "tags": row[3]}
    cur.execute("DELETE FROM notes WHERE id = ?", (row[0],))
    conn.commit()
    conn.close()
    sync_notes_to_markdown()
    return del_note

def delete_note_by_keyword(keyword: str) -> bool:
    """Удаляет первую подходящую заметку по ключевому слову."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM notes WHERE ru_lower(content) LIKE ? ORDER BY id DESC LIMIT 1",
                (f"%{keyword.lower()}%",))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    cur.execute("DELETE FROM notes WHERE id = ?", (row[0],))
    conn.commit()
    conn.close()
    sync_notes_to_markdown()
    return True

def clear_all_notes() -> int:
    """Полностью очищает все заметки."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM notes")
    cnt = cur.fetchone()[0]
    cur.execute("DELETE FROM notes")
    conn.commit()
    conn.close()
    sync_notes_to_markdown()
    return cnt


def parse_organizer_commands(user_msg: str, persona: str = "melvin"):
    s = user_msg.lower().strip()

    # -------------------------------------------------------------
    # А. БУДИЛЬНИКИ
    # -------------------------------------------------------------
    # Отмена всех будильников
    if any(k in s for k in ["удали все будильники", "отмени все будильники", "сбрось будильники", "выключи все будильники"]):
        clear_all_alarms()
        reply = "*рыгает* Снес все будильники к чертям. Спи сколько влезет, Морти." if persona == "rick" else "Все активные будильники деактивированы и удалены из реестра."
        return {"type": "alarm", "action": "clear_all", "reply": reply, "tool_used": "organizer_alarm"}

    # Список будильников
    if any(k in s for k in ["какие будильники", "список будильников", "что с будильниками", "будильники стоят"]):
        alarms = list_alarms()
        if not alarms:
            reply = "*рыгает* Никаких будильников нет, спи спокойно." if persona == "rick" else "В реестре нет ни одного активного будильника."
        else:
            times = ", ".join(a["time_str"] for a in alarms)
            reply = f"*рыгает* У тебя стоят будильники на {times}. Не проспи, гений." if persona == "rick" else f"Активные будильники: {times}. Модуль контроля сна активен."
        return {"type": "alarm", "action": "list", "alarms": alarms, "reply": reply, "tool_used": "organizer_alarm"}

    # Установка будильника: "поставь будильник на 7:30", "разбуди меня в 8 утра"
    is_alarm_set = any(k in s for k in ["будильник", "разбуди", "проснись", "подъем"])
    if is_alarm_set and any(k in s for k in ["на", "в", "поставь", "заведи"]):
        h, m = parse_time_hh_mm(s)
        if h is not None:
            res = set_alarm(h, m)
            t_str = res["time_str"]
            if persona == "rick":
                reply = f"*рыгает* Поставил будильник на {t_str}. Если опять нажмешь 'отложить', я заставлю этот динамик орать на ультразвуке."
            else:
                reply = f"Будильник на {t_str} установлен. В назначенный час акустический импульс прервет твой биологический сон."
            return {"type": "alarm", "action": "set", "time_str": t_str, "reply": reply, "tool_used": "organizer_alarm"}

    # -------------------------------------------------------------
    # Б. НАПОМИНАНИЯ
    # -------------------------------------------------------------
    # Список напоминаний
    if any(k in s for k in ["какие напоминания", "список напоминаний", "что напомнить", "мои напоминания"]):
        rems = list_reminders(only_pending=True)
        if not rems:
            reply = "*рыгает* Напоминаний нет. Твоя пустая голова свободна от забот." if persona == "rick" else "Список напоминаний пуст. Никаких отложенных задач не зафиксировано."
        else:
            items_str = "; ".join(f"{r['time']} — {r['text']}" for r in rems)
            reply = f"*рыгает* Вот что записано: {items_str}. Смотри не забудь." if persona == "rick" else f"Запланированные напоминания: {items_str}."
        return {"type": "reminder", "action": "list", "reminders": rems, "reply": reply, "tool_used": "organizer_reminder"}

    # Очистка напоминаний
    if any(k in s for k in ["очисти напоминания", "удали все напоминания", "сбрось напоминания"]):
        clear_all_reminders()
        reply = "*рыгает* Стер все твои напоминалки. Чистый лист." if persona == "rick" else "Реестр напоминаний полностью очищен."
        return {"type": "reminder", "action": "clear_all", "reply": reply, "tool_used": "organizer_reminder"}

    # Создание напоминания: "напомни через 30 минут выключить суп", "напомни в 18:00 купить молоко"
    if "напомни" in s or "напомнить" in s:
        # 1. Относительное время: "через N минут / часов"
        m_rel_min = re.search(r'через\s+(\d+)\s*(?:минут(?:у|ы)?|мин)\s+(.*)', s)
        if m_rel_min:
            mins = int(m_rel_min.group(1))
            task_text = m_rel_min.group(2).strip()
            res = set_reminder_relative(mins * 60, task_text)
            reply = f"*рыгает* Засек {mins} минут. Напомню про «{task_text}» ровно в {res['time_str']}." if persona == "rick" else f"Напоминание зафиксировано: через {mins} мин ({res['time_str']}) сообщу: «{task_text}»."
            return {"type": "reminder", "action": "set", "time_str": res["time_str"], "text": task_text, "reply": reply, "tool_used": "organizer_reminder"}

        m_rel_hr = re.search(r'через\s+(\d+)\s*(?:час(?:а|ов)?|ч)\s+(.*)', s)
        if m_rel_hr:
            hrs = int(m_rel_hr.group(1))
            task_text = m_rel_hr.group(2).strip()
            res = set_reminder_relative(hrs * 3600, task_text)
            reply = f"*рыгает* Напомню про «{task_text}» через {hrs} ч, в {res['time_str']}." if persona == "rick" else f"Напоминание установлено на {res['time_str']}: «{task_text}»."
            return {"type": "reminder", "action": "set", "time_str": res["time_str"], "text": task_text, "reply": reply, "tool_used": "organizer_reminder"}

        # 2. Абсолютное время: "в 18:30 купить молоко"
        h, m = parse_time_hh_mm(s)
        if h is not None:
            # Вырезаем текст задачи: убираем "напомни", время и предлог "в"
            clean_text = re.sub(r'напомни(?:ть)?\s*(?:мне)?\s*(?:в\s+)?([01]?\d|2[0-3])[:\.\s]([0-5]\d)?\s*(?:утра|вечера|дня|ночи)?\s*(?:о\s+том,\s*что|что|про|о)?', '', s).strip()
            if not clean_text: clean_text = "Событие по расписанию"
            res = set_reminder_absolute(h, m, clean_text)
            reply = f"*рыгает* Записал: в {res['time_str']} напомню про «{clean_text}». Не благодари." if persona == "rick" else f"Напоминание зарегистрировано: в {res['time_str']} выдам оповещение: «{clean_text}»."
            return {"type": "reminder", "action": "set", "time_str": res["time_str"], "text": clean_text, "reply": reply, "tool_used": "organizer_reminder"}

    # -------------------------------------------------------------
    # В. СПИСКИ ДЕЛ И ПОКУПОК (TO-DO & SHOPPING)
    # -------------------------------------------------------------
    is_shopping = any(k in s for k in ["покупок", "купить", "в магазине", "продуктов"])
    category = "shopping" if is_shopping else "tasks"
    cat_name = "покупок" if is_shopping else "дел"

    # 1. Добавить в список: "добавь в список покупок: хлеб, молоко, сыр"
    if any(k in s for k in ["добавь в список", "добавь в покупки", "запиши в список", "занеси в список", "надо купить", "надо сделать"]):
        raw_items = re.sub(r'^(?:добавь в список|добавь в покупки|запиши в список|занеси в список|надо купить|надо сделать)\s*(?:покупок|дел)?[:\s]*', '', s).strip()
        split_items = re.split(r'[,;\n]|\s+и\s+', raw_items)
        valid_items = [it.strip() for it in split_items if len(it.strip()) >= 2]
        if valid_items:
            added = add_todos(valid_items, category=category)
            items_str = ", ".join(added)
            reply = f"*рыгает* Записал в список {cat_name}: {items_str}. Надеюсь, ты это реально сделаешь." if persona == "rick" else f"В список {cat_name} добавлены позиции: {items_str}."
            return {"type": "todo", "action": "add", "category": category, "items": added, "reply": reply, "tool_used": "organizer_todo"}

    # 2. Вычеркнуть / завершить пункт: "вычеркни сыр", "купил хлеб", "удали из списка молоко"
    if any(k in s for k in ["вычеркни", "удали из списка", "сделано", "купил", "выполнил"]):
        clean_target = re.sub(r'^(?:вычеркни|удали из списка|сделано|купил|выполнил)\s*(?:покупок|дел)?\s*', '', s).strip()
        if clean_target:
            ok = complete_todo_item(clean_target)
            if ok:
                reply = f"*рыгает* Вычеркнул «{clean_target}» из списка. На один пункт меньше." if persona == "rick" else f"Пункт «{clean_target}» отмечен как выполненный."
            else:
                reply = f"*рыгает* Не нашел «{clean_target}» в списке, проверь глаза." if persona == "rick" else f"Элемент «{clean_target}» в активных списках не обнаружен."
            return {"type": "todo", "action": "complete", "item": clean_target, "reply": reply, "tool_used": "organizer_todo"}

    # 3. Очистить список
    if any(k in s for k in ["очисти список", "удали весь список", "сбрось список", "очисти покупки", "очисти список покупок", "очисти список дел"]):
        clear_todos(category)
        reply = f"*рыгает* Список {cat_name} обнулен. Можешь ничего не делать." if persona == "rick" else f"Список {cat_name} полностью очищен."
        return {"type": "todo", "action": "clear", "category": category, "reply": reply, "tool_used": "organizer_todo"}

    # 4. Прочитать список: "что в списке покупок", "прочитай список дел"
    if any(k in s for k in ["что в списке", "прочитай список", "покажи список", "список дел", "список покупок", "какие дела"]):
        items = list_todos(category)
        if not items:
            reply = f"*рыгает* В списке {cat_name} шаром покати. Ни одной записи." if persona == "rick" else f"Список {cat_name} пуст. Задач нет."
        else:
            formatted = ", ".join(f"{idx+1}) {it['text']}" for idx, it in enumerate(items))
            reply = f"*рыгает* Твой список {cat_name}: {formatted}." if persona == "rick" else f"В списке {cat_name} значатся: {formatted}."
        return {"type": "todo", "action": "list", "category": category, "items": items, "reply": reply, "tool_used": "organizer_todo"}

    # -------------------------------------------------------------
    # Г. ГОЛОСОВЫЕ ЗАМЕТКИ И МЫСЛИ (NOTES & THOUGHT ARCHIVE)
    # -------------------------------------------------------------
    # 1. Очистить все заметки
    if any(k in s for k in ["очисти все заметки", "удали все заметки", "сбрось все заметки"]):
        c = clear_all_notes()
        reply = "*рыгает* Снес все твои заметки к чертям, notes.md пуст. Начинай с чистого листа, Морти." if persona == "rick" else f"Реестр заметок очищен ({c} записей удалено). Файл notes.md обновлен."
        return {"type": "note", "action": "clear_all", "count": c, "reply": reply, "tool_used": "organizer_note"}

    # 2. Удалить последнюю заметку
    if any(k in s for k in ["удали последнюю заметку", "сотри последнюю заметку", "удали последнюю мысль"]):
        del_n = delete_last_note()
        if del_n:
            reply = f"*рыгает* Стер последнюю заметку «{del_n['content']}». Больше ее нет." if persona == "rick" else f"Последняя заметка «{del_n['content']}» безвозвратно удалена."
        else:
            reply = "*рыгает* В архиве и так шаром покати, нечего удалять." if persona == "rick" else "Список заметок пуст, удаление невозможно."
        return {"type": "note", "action": "delete_last", "note": del_n, "reply": reply, "tool_used": "organizer_note"}

    # 3. Удалить конкретную заметку по ключевому слову
    if any(s.startswith(k) for k in ["удали заметку про", "удали заметку о", "сотри заметку про", "удали мысль про"]):
        kw = re.sub(r'^(?:удали|сотри)\s+(?:заметку|мысль)\s+(?:про|о|об)\s*', '', s).strip()
        if kw:
            ok = delete_note_by_keyword(kw)
            if ok:
                reply = f"*рыгает* Выкинул заметку про «{kw}» на свалку истории." if persona == "rick" else f"Заметка по запросу «{kw}» успешно удалена."
            else:
                reply = f"*рыгает* Нет такой заметки про «{kw}», Морти." if persona == "rick" else f"Заметка, содержащая «{kw}», в архиве не найдена."
            return {"type": "note", "action": "delete_by_keyword", "keyword": kw, "reply": reply, "tool_used": "organizer_note"}

    # 4. Прочитать последнюю заметку
    if any(k in s for k in ["последняя заметка", "прочитай последнюю заметку", "что я записал последнее", "какая последняя мысль", "что в последней заметке"]):
        last_n = get_last_note()
        if last_n:
            reply = f"*рыгает* Твоя последняя гениальная мысль от {last_n['created_at']}: «{last_n['content']}»." if persona == "rick" else f"Последняя запись от {last_n['created_at']}: «{last_n['content']}»."
        else:
            reply = "*рыгает* Заметок нет вообще. Ты ничего не записывал." if persona == "rick" else "В архиве нет сохраненных заметок."
        return {"type": "note", "action": "get_last", "note": last_n, "reply": reply, "tool_used": "organizer_note"}

    # 5. Поиск в заметках
    if any(k in s for k in ["найди заметку", "поиск в заметках", "что я записывал про", "что я думал про", "найди мысль"]):
        query = re.sub(r'^(?:найди|поиск в|что я записывал|что я думал|найди в)?\s*(?:заметку|заметках|мысль)?\s*(?:про|о|об|со словом)?\s*', '', s).strip()
        if query:
            found = search_notes(query)
            if found:
                items_str = "; ".join(f"{n['created_at']}: «{n['content']}»" for n in found[:3])
                reply = f"*рыгает* Нашел вот что: {items_str}." if persona == "rick" else f"По запросу «{query}» найдено записей: {len(found)}. {items_str}."
            else:
                reply = f"*рыгает* Ничего про «{query}» в твоих каракулях нет." if persona == "rick" else f"По запросу «{query}» совпадений не обнаружено."
            return {"type": "note", "action": "search", "query": query, "found": found, "reply": reply, "tool_used": "organizer_note"}

    # 6. Список всех заметок
    if any(k in s for k in ["прочитай заметки", "прочитай мои заметки", "все заметки", "список заметок", "какие у меня заметки", "какие заметки", "что в заметках", "покажи заметки", "мои мысли", "мои заметки", "что я записал"]):
        notes = list_notes(limit=5)
        if not notes:
            reply = "*рыгает* Твой архив заметок пуст, как и голова." if persona == "rick" else "Архив заметок пуст. Диктуй: «запиши заметку [текст]»."
        else:
            items_str = "; ".join(f"{n['created_at']} — {n['content']}" for n in notes)
            reply = f"*рыгает* Вот твои последние заметки: {items_str}." if persona == "rick" else f"В архиве {len(notes)} последних заметок: {items_str}."
        return {"type": "note", "action": "list", "notes": notes, "reply": reply, "tool_used": "organizer_note"}

    # 7. Создать заметку: "создай заметку ...", "запиши заметку ...", "сохрани мысль ...", "заметка: ...", "запиши в блокнот ..."
    is_note_cmd = any(s.startswith(k) for k in [
        "создай заметку", "сделай заметку", "добавь заметку", "напиши заметку",
        "запиши заметку", "сохрани заметку", "новая заметка", "заметка:", "заметка ",
        "сохрани мысль", "запиши мысль", "запиши в блокнот", "заметка в блокнот",
        "зафиксируй мысль", "мысль:"
    ])
    if is_note_cmd:
        note_body = re.sub(r'^(?:создай заметку|сделай заметку|добавь заметку|напиши заметку|запиши заметку|сохрани заметку|новая заметка|заметка:|заметка|сохрани мысль|запиши мысль|запиши в блокнот|заметка в блокнот|зафиксируй мысль|мысль:)\s*[:\s]*', '', s).strip()
        if len(note_body) >= 2:
            res = add_note(note_body)
            reply = f"*рыгает* Записал твою мысль: «{note_body}». Положил в notes.md, Морти. Не потеряй." if persona == "rick" else f"Заметка сохранена: «{note_body}». Синхронизировал с notes.md. Твоя память спасена."
            return {"type": "note", "action": "add", "note": res, "reply": reply, "tool_used": "organizer_note"}



    return None

# =========================================================================
# 5. ФОНОВЫЙ МОНИТОР БУДИЛЬНИКОВ И НАПОМИНАНИЙ (DAEMON LOOP)
# =========================================================================

_scheduler_running = False

def check_pending_alerts():
    """Проверяет будильники и напоминания, заносит сработавшие в очередь TRIGGERED_ALERTS."""
    now = datetime.datetime.now()
    now_hh_mm = now.strftime("%H:%M")
    now_ts = now.timestamp()

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # 1. Проверка будильников (совпадение HH:MM в пределах текущей минуты)
        cur.execute("SELECT id, time_str, label FROM alarms WHERE is_active = 1 AND time_str = ?", (now_hh_mm,))
        triggered_alarms = cur.fetchall()
        for al in triggered_alarms:
            # Чтобы не орать каждую секунду минуты, отключаем или дедуплицируем
            alert_id = f"alarm_{al[0]}_{now.day}_{now_hh_mm}"
            if not any(a.get("alert_id") == alert_id for a in TRIGGERED_ALERTS):
                TRIGGERED_ALERTS.append({
                    "alert_id": alert_id,
                    "type": "alarm",
                    "time_str": al[1],
                    "label": al[2],
                    "timestamp": now_ts
                })

        # 2. Проверка напоминаний (target_timestamp <= now_ts)
        cur.execute("SELECT id, remind_time_str, text FROM reminders WHERE is_done = 0 AND target_timestamp <= ?", (now_ts,))
        triggered_rems = cur.fetchall()
        for rm in triggered_rems:
            alert_id = f"reminder_{rm[0]}"
            if not any(a.get("alert_id") == alert_id for a in TRIGGERED_ALERTS):
                TRIGGERED_ALERTS.append({
                    "alert_id": alert_id,
                    "type": "reminder",
                    "id": rm[0],
                    "time_str": rm[1],
                    "text": rm[2],
                    "timestamp": now_ts
                })
            # Помечаем выполненным в БД
            cur.execute("UPDATE reminders SET is_done = 1 WHERE id = ?", (rm[0],))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Organizer Scheduler Error]: {e}")

def pop_triggered_alerts() -> list:
    """Забирает сработавшие алерты для фронтенда/голосового движка."""
    global TRIGGERED_ALERTS
    alerts = list(TRIGGERED_ALERTS)
    TRIGGERED_ALERTS.clear()
    return alerts

def _scheduler_loop():
    while _scheduler_running:
        check_pending_alerts()
        time.sleep(4)

def start_organizer_scheduler():
    global _scheduler_running
    if not _scheduler_running:
        _scheduler_running = True
        t = threading.Thread(target=_scheduler_loop, daemon=True)
        t.start()
        print("[OrganizerEngine] Background Alarm & Reminder scheduler started!")

if __name__ == "__main__":
    init_organizer_db()
    print("Test set alarm:", set_alarm(7, 30))
    print("Test list alarms:", list_alarms())
    print("Test parse alarm command:", parse_organizer_commands("поставь будильник на 8:00", "rick"))
    print("Test add todo:", parse_organizer_commands("добавь в список покупок хлеб, сыр и яблоки", "melvin"))
    print("Test list todos:", parse_organizer_commands("что в списке покупок", "rick"))
    print("Test complete todo:", parse_organizer_commands("вычеркни сыр", "melvin"))
    print("Test set reminder:", parse_organizer_commands("напомни через 15 минут выключить духовку", "rick"))
