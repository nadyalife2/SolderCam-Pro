#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import time
import sqlite3
import requests

DB_PATH = "datasets/omni_knowledge.db"
NODE1_URL = "http://127.0.0.1:8080/completion"

def search_rag(query: str, limit: int = 1) -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Очищаем от спецсимволов для синтаксиса FTS5
    clean_query = re.sub(r'[^\w\s]', ' ', query)
    words = [w for w in clean_query.split() if len(w) > 3]
    terms = " OR ".join(f'"{w}"' for w in words)
    c.execute("""
    SELECT title, content FROM articles_fts 
    WHERE articles_fts MATCH ? 
    ORDER BY rank LIMIT ?
    """, (terms, limit))
    rows = c.fetchall()
    conn.close()
    if not rows:
        return ""
    # Отрезаем компактный контекст до 400 символов (~90 токенов) для скорости вычисления на CPU
    title, content = rows[0]
    return f"Источник ({title}):\n{content[:400]}"

def run_rag_test(user_question: str):
    print(f"\n❓ Вопрос пользователя: '{user_question}'")
    
    # 1. Локальный оффлайн RAG поиск
    t0 = time.perf_counter()
    context = search_rag(user_question)
    dt_rag = (time.perf_counter() - t0) * 1000
    print(f"  🔍 [Local RAG] Найдено в omni_knowledge.db за {dt_rag:.2f} мс!")

    # 2. Формирование промпта с инъекцией пустого блока <think>
    sys_prompt = "<|im_start|>system\nТы эксперт кластера Triad-Omni. Используй контекст для точного ответа.<|im_end|>\n"
    user_part = f"<|im_start|>user\nКонтекст:\n{context}\n\nВопрос: {user_question}<|im_end|>\n<|im_start|>assistant\n<think>\n</think>\n"
    
    payload = {
        "prompt": sys_prompt + user_part,
        "n_predict": 100,
        "temperature": 0.2,
        "cache_prompt": True,
        "stop": ["<|im_end|>", "<|endoftext|>"]
    }

    # 3. Запрос к Xiaomi Mi 10T
    t1 = time.perf_counter()
    r = requests.post(NODE1_URL, json=payload, timeout=120)
    dt_llm = time.perf_counter() - t1
    data = r.json()
    
    print(f"  ⚡ [Xiaomi Mi 10T 9B] Ответ сгенерирован за: {dt_llm:.2f} сек!")
    print(f"  📝 Ответ:\n{data.get('content', '').strip()}")

if __name__ == "__main__":
    run_rag_test("Как отключить зарядку батареи на Xiaomi Mi 10T через sysfs при работе 24/7?")
