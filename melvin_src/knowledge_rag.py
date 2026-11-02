import sqlite3
import re
import os

DB_PATH = "/melvin/data/knowledge.db"
if not os.path.exists(os.path.dirname(DB_PATH)):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_knowledge_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    # Таблица FTS5 с триграммным токенизатором
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS kb_facts USING fts5(
            topic,
            content,
            tokenize='trigram'
        );
    """)
    conn.commit()

    # Начальное наполнение базовыми фактами о лоре Рика и железе, если пусто
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM kb_facts")
    count = cur.fetchone()[0]
    if count == 0:
        seed_data = [
            ("рик", "Рик Санчез C-137 — гениальный ученый-мизантроп, создатель портальной пушки, способной перемещаться между бесконечными альтернативными вселенными."),
            ("морти", "Морти Смит — четырнадцатилетний внук Рика, часто сопровождающий его в смертельно опасных межпространственных приключениях."),
            ("портальная пушка", "Портальная пушка работает на концентрированной темной материи и зеленой жидкости, открывая кротовые норы в пространстве-времени."),
            ("цитадель", "Цитадель Риков — секретная межпространственная станция, созданная Риками из параллельных измерений для защиты от угроз."),
            ("helio x20", "Чипсет MediaTek Helio X20 MT6797 содержит 10 ядер в трех кластерах: 2 ядра Cortex-A72 на 2.1 ГГц и 8 ядер Cortex-A53."),
            ("redmi note 4", "Xiaomi Redmi Note 4 Nikel оснащен аккумулятором емкостью 4100 мАч и 3 ГБ оперативной памяти LPDDR3."),
            ("вселенная", "Мультивселенная бесконечна, вселенная бессмысленна, а квантовая флуктуация определяет рождение новых звезд.")
        ]
        cur.executemany("INSERT INTO kb_facts (topic, content) VALUES (?, ?)", seed_data)
        conn.commit()

    conn.close()

def search_knowledge(query: str, max_chars: int = 250) -> str:
    """Быстрый поиск факта в FTS5 без эмбеддеров за 1-2 мс."""
    clean_words = re.findall(r"[а-яa-z0-9]{3,}", query.lower())
    if not clean_words:
        return ""

    match_expr = " OR ".join(clean_words[:5])

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT content FROM kb_facts 
            WHERE kb_facts MATCH ? 
            ORDER BY bm25(kb_facts, 2.0, 8.0) ASC 
            LIMIT 1
        """, (match_expr,))
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return row[0][:max_chars].strip()
    except Exception as e:
        print(f"[RAG notice]: {e}")
    return ""

def add_fact(topic: str, content: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO kb_facts (topic, content) VALUES (?, ?)", (topic, content))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[RAG add error]: {e}")
