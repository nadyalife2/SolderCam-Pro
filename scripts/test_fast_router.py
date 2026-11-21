#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import requests
from omni_fast_router_v4_9 import handle_tier0, FAST_PATTERNS, evaluate_complexity, build_node1_payload

print("🧪 ТЕСТИРОВАНИЕ TIER 0 FAST-PATH...")
queries = ["статус", "температура", "батарея", "аптайм", "привет"]

for q in queries:
    t0 = time.perf_counter()
    matched = False
    for pat, label in FAST_PATTERNS:
        if pat.match(q):
            ans = handle_tier0(label)
            dt_ms = (time.perf_counter() - t0) * 1000
            print(f"  [Tier 0] Запрос: '{q}' -> Время: {dt_ms:.3f} мс | Ответ: {ans[:60]}...")
            matched = True
            break
    if not matched:
        print(f"  [MISMATCH] {q}")

print("\n🧪 ТЕСТИРОВАНИЕ ОЦЕНКИ СЛОЖНОСТИ (COMPLEXITY SCORE)...")
test_prompts = [
    ("Привет, как дела?", False),
    ("Сколько ядер у процессора Snapdragon 865?", False),
    ("Почему троттлит ядро Cortex-A77 и как оптимизировать регистры PMIC?", True),
    ("Напиши скрипт на Bash для автоматической перезагрузки ADB демона при падении", True)
]

for p, expected_think in test_prompts:
    think, score = evaluate_complexity(p)
    status = "✅" if think == expected_think else "⚠️"
    print(f"  {status} Запрос: '{p[:45]}...' -> Sc = {score:.2f} | Thinking: {think}")

print("\n🧪 ТЕСТИРОВАНИЕ ЗАПРОСА В УЗЕЛ №1 С ПРЕФИКСОМ <think>\\n</think>\\n...")
payload = build_node1_payload("Назови модель процессора в Xiaomi Mi 10T", enable_thinking=False)
t0 = time.perf_counter()
try:
    r = requests.post("http://127.0.0.1:8080/completion", json=payload, timeout=30)
    dt = time.perf_counter() - t0
    data = r.json()
    print(f"  ⚡ Ответ получен за: {dt:.2f} сек!")
    print(f"  📝 Текст ответа: {data.get('content', '').strip()}")
except Exception as e:
    print(f"  ❌ Ошибка подключения к Mi 10T: {e}")
