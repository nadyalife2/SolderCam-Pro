#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brand Voice & Anti-Slop Analyzer for Triad-Omni
Проверяет соответствие текстов авторскому стилю MASTER EDITORIAL BOOK:
Глава 2. Мой голос — Practico (редакция 2):
- Женский род прошедшего времени («собрала», «раскопала», «проверила», «протестировала»)
- Категорические стоп-фразы («идеальный результат», «абсолютно безопасно», «проще простого»)
- Отсутствие бюрократического канцелярита и вульгарного жаргона («короче», «урвал», «сдыхает»)
- Отсутствие вопросов к читателю в финале («А что думаете Вы?»)
- Высокая плотность инженерных фактов (мс, МГц, °C, регистры, шины, дампы)
"""

import sys
import re
from pathlib import Path

# Канцеляризмы и «вода» (AI Slop markers)
BANNED_WORDS = [
    r"является важным", r"следует отметить", r"в современном мире",
    r"нельзя не упомянуть", r"играет ключевую роль", r"как известно",
    r"во избежание проблем", r"данный аспект", r"представляет собой",
    r"в данной статье мы рассмотрели", r"в этой статье мы",
    r"подводя итоги", r"как мы увидели"
]

# Жаргон ради эффекта (недопустим по стандарту Practico 2.3)
BANNED_JARGON = [
    r"\bкороче\b", r"\bурвал\b", r"\bурвала\b", r"\bсдыхает\b", r"\bвскрытие трупа\b"
]

# Стоп-фразы из Главы 2.10
STOP_PHRASES = [
    r"идеальный результат",
    r"абсолютно безопасно",
    r"без каких-либо рисков",
    r"справится любой за минуту",
    r"проще простого",
    r"гарантированный результат",
    r"это можно делать как угодно",
    r"ошибиться невозможно",
    r"невозможно обмануть",
    r"подойд[её]т всем без исключения",
    r"секретный секрет"
]

# Маркеры мужского рода прошедшего времени (когда автор говорит о себе)
MALE_VERBS = [
    r"\bя сделал\b", r"\bя собрал\b", r"\bя раскопал\b", r"\bя проверил\b",
    r"\bя протестировал\b", r"\bя написал\b", r"\bя настроил\b", r"\bя прошил\b",
    r"\bя замерил\b", r"\bя подключил\b", r"\bя вывел\b"
]

# Желательные маркеры авторского голоса (женский род)
FEMALE_VERBS = [
    r"\bя сделала\b", r"\bя собрала\b", r"\bя раскопала\b", r"\bя проверила\b",
    r"\bя протестировала\b", r"\bя написала\b", r"\bя настроила\b", r"\bя прошила\b",
    r"\bя замерила\b", r"\bя подключила\b", r"\bя вывела\b"
]

def analyze_text(text: str) -> dict:
    slop_matches = []
    for pattern in BANNED_WORDS:
        found = re.findall(pattern, text, re.I)
        if found:
            slop_matches.extend(found)

    jargon_matches = []
    for pattern in BANNED_JARGON:
        found = re.findall(pattern, text, re.I)
        if found:
            jargon_matches.extend(found)

    stop_matches = []
    for pattern in STOP_PHRASES:
        found = re.findall(pattern, text, re.I)
        if found:
            stop_matches.extend(found)

    male_matches = []
    for pattern in MALE_VERBS:
        found = re.findall(pattern, text, re.I)
        if found:
            male_matches.extend(found)

    female_count = 0
    for pattern in FEMALE_VERBS:
        female_count += len(re.findall(pattern, text, re.I))

    # Проверка финала на дежурный вопрос к читателю
    tail = text.strip().splitlines()[-3:] if text.strip() else []
    tail_text = " ".join(tail).lower()
    has_ending_question = bool(re.search(r'(пишите в комментариях|что думаете вы|ваше мнение|а как вы|подписывайтесь)\??', tail_text))

    # Плотность фактов (числа, мс, °C, пути, команды, регистры)
    facts = re.findall(r'(\d+\.?\d*\s*(?:мс|ms|°C|ГБ|GB|MB|мА|V|fps|Hz|кГц|kHz)|\/sys\/[^\s]+|0x[0-9a-fA-F]+|`[^`]+`)', text)

    score = 100
    score -= len(slop_matches) * 15
    score -= len(jargon_matches) * 10
    score -= len(stop_matches) * 20
    score -= len(male_matches) * 25
    if has_ending_question:
        score -= 20
    if female_count == 0 and ("я " in text.lower()):
        score -= 10

    return {
        "score": max(0, score),
        "status": "💎 Идеальный Practico v2" if score >= 85 else ("⚠️ Нужна доработка" if score >= 60 else "❌ Требуется переписать"),
        "female_verb_count": female_count,
        "male_verb_violations": male_matches,
        "slop_phrases": slop_matches,
        "jargon_violations": jargon_matches,
        "stop_phrase_violations": stop_matches,
        "has_ending_question": has_ending_question,
        "fact_density_count": len(facts)
    }

def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.exists():
            text = path.read_text(encoding='utf-8')
        else:
            text = " ".join(sys.argv[1:])
    else:
        text = "Я раскопала драйвер PMIC PM8150B и собрала прямое питание 4.18V. Задержка составила 0.016 мс при температуре 34°C."

    res = analyze_text(text)
    print(f"📊 Оценка соответствия стилю: {res['score']}/100 — {res['status']}")
    print(f"  • Женских глаголов от первого лица: {res['female_verb_count']}")
    print(f"  • Плотность фактов/параметров: {res['fact_density_count']}")
    if res['male_verb_violations']:
        print(f"  ❌ Ошибки рода (найден мужской род): {res['male_verb_violations']}")
    if res['stop_phrase_violations']:
        print(f"  ⛔ Стоп-фразы Practico 2.10: {res['stop_phrase_violations']}")
    if res['jargon_violations']:
        print(f"  ⚠️ Запрещенный просторечный жаргон: {res['jargon_violations']}")
    if res['slop_phrases']:
        print(f"  ⚠️ Вода и канцеляризмы: {res['slop_phrases']}")
    if res['has_ending_question']:
        print("  ⛔ Нарушение 2.9: найден дежурный вопрос читателю или призыв в комментариях в конце статьи")

if __name__ == "__main__":
    main()
