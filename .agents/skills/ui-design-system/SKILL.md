---
name: ui-design-system
description: Systematic token architecture, color semantics, typography scales, spacing rules, and state machines (Loading, Empty, Error, Active) for technical HUD dashboards and dark-mode web interfaces.
version: 1.0.0
---

# UI Design System & Token Architecture

Стандарты дизайн-системы для всех веб-интерфейсов и экранных терминалов проекта.

## Токены палитры (Industrial OLED Cyberdeck):
- `--bg-primary: #090d16` (глубокий черный с синим подтоном).
- `--bg-surface: #111827` (фон карточек и панелей).
- `--border-subtle: #1f2937` (тонкая 1px граница).
- `--color-active: #00ffcc` (неоновый циан — рабочий статус).
- `--color-ok: #00ff88` (изумрудный зеленый — 200 OK / норма).
- `--color-warn: #ffaa00` (янтарный — внимание/нагрев).
- `--color-err: #ff3366` (карминовый красный — оффлайн/сбой).

## Состояния компонентов (State Matrix):
Каждый интерактивный блок обязан обрабатывать 4 состояния:
1. **Empty State:** Информативная подсказка с кнопкой первичного действия.
2. **Loading State:** Скелетон или пульсирующий индикатор без дергания макета.
3. **Active/Healthy State:** Четкие параметры с единицами измерения.
4. **Error State:** Понятный диагноз ошибки на человеческом языке и кнопка повтора.
