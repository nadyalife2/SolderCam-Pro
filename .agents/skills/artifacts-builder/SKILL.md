---
name: artifacts-builder
description: Builds self-contained, interactive single-file HTML/SVG visual artifacts, architecture diagrams, live dashboards, and reactive widgets with zero external script dependencies.
version: 1.0.0
---

# Interactive Artifacts Builder

Создание самодостаточных интерактивных HTML/SVG артефактов для наглядной демонстрации архитектуры кластера.

## Принципы:
1. **Zero External Dependencies:** Никаких CDN (`cdn.jsdelivr.net`, `unpkg.com`), которые могут отвалиться без интернета. Все стили и скрипты встроены инлайн.
2. **SVG & Canvas Data Visualizations:** Графики температуры, распределения нагрузки ядер и времени отклика рисуются нативными средствами браузера.
3. **Мобильная адаптивность:** Артефакт одинаково читаем как в окне браузера ПК, так и на 6.67" экране смартфона Mi 10T.
