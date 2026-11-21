---
name: product-manager
description: Product Requirements Documents (PRD), Lean Canvas formulation, user persona discovery, and feature prioritization using the RICE scoring model via rice_prioritizer.py.
version: 1.0.0
---

# Product Management & RICE Framework

Управление продуктом для аппаратных и программных проектов кластера.

## Приоритизация по RICE:
Запуск скрипта скоринга фичей:
```bash
python scripts/rice_prioritizer.py
```

## Структура Product Requirements Document (PRD):
1. **Problem Statement:** Какую конкретную боль инженера или пользователя мы решаем?
2. **Success Metrics (KPI):**
   - Задержка первого токена (TTFT) < 1.2 с на смартфоне.
   - Температура батареи при нагрузке < 38°C.
   - Число активных сессий без вылетов 24/7 > 99.9%.
3. **User Stories:** «Как мастер по пайке, я хочу видеть температуру жала и процессора прямо в углу видоискателя, чтобы не отвлекаться от микроскопа».
4. **Out of Scope (Чего мы НЕ делаем):** Жесткие границы релиза, чтобы не утонуть в бесконечной разработке.
