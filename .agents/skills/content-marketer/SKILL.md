---
name: content-marketer
description: Organic distribution strategy, content repurposing (turning longform technical articles into viral Telegram/Habr/Reddit/VC posts), editorial calendar planning, and audience growth for open-source AI projects.
version: 1.0.0
---

# Content Marketing & Repurposing Pipeline

Пайплайн дистрибуции инженерных наработок Triad-Omni на внешние площадки.

## Матрица переупаковки (Content Atomization):
Одна большая статья из `ARTICLES/` (например, 42 статьи) превращается в:
1. **Лонгрид на Habr / VC.ru:** Полный разбор архитектуры, графики производительности, схемотехника питания и замеры задержек.
2. **Серия постов в Telegram (3-5 частей):**
   - Пост 1: Инженерный фейл и грабли («Как вздуваются батареи на серверах из телефонов и как мы это решили через sysfs»).
   - Пост 2: Решение («Команда `battery_charging_enabled=0` и DC-DC прямое питание»).
   - Пост 3: Ссылка на открытый репозиторий и скриншот дашборда.
3. **Тред в X (Twitter) / Reddit (r/LocalLLaMA, r/androiddev):**
   - Короткий твит с видео или бенчмарком: «Running Qwen3.5-9B locally on Snapdragon 865 with 0.016ms fast-router».
