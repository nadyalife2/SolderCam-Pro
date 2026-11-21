---
name: tailwind-patterns
description: Modern Tailwind CSS v4 patterns, CSS-first token configuration, container queries, zero-runtime overhead, and anti-slop guidelines for lightweight web dashboards, cyberdeck HUDs, and on-device web interfaces.
version: 1.0.0
---

# Tailwind CSS v4 Architecture & Anti-Slop Guidelines

Стандарты проектирования веб-интерфейсов для дашбордов кластера Triad-Omni (порты `:8000`, `:8090`).

## 1. Концепция CSS-First (Tailwind v4)

В Tailwind v4 отменяется тяжелый JavaScript-конфиг `tailwind.config.js`. Все токены объявляются через нативную директиву `@theme` в чистом CSS:

```css
@theme {
  --color-hud-bg: #090d16;
  --color-hud-surface: #111827;
  --color-hud-border: #1f2937;
  --color-hud-cyan: #00ffcc;
  --color-hud-green: #00ff88;
  --color-hud-red: #ff3366;
  --color-hud-yellow: #ffaa00;
  
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
```

---

## 2. Борьба с «AI Slop» (Запрещенные шаблоны)

1. **Никаких случайных фиолетовых градиентов:**
   - *Запрещено:* `bg-gradient-to-r from-purple-500 to-indigo-600` повсюду.
   - *Разрешено:* чистый глубокий фон с акцентной контурной подсветкой (1px border + box-shadow glow).
2. **Отказ от произвольных значений (Arbitrary Spam):**
   - Не писать `w-[342px] mt-[13px] text-[11px]`. Использовать строгую сетку кратности 4 (`gap-4`, `p-3`, `text-xs`, `text-sm`).
3. **Контейнерные запросы (`@container`) вместо `@media`:**
   - Карточки нод кластера должны реагировать на ширину своего родительского блока, а не на ширину всего экрана:
   ```html
   <div class="@container">
     <div class="flex flex-col @sm:flex-row justify-between items-center">
       ...
     </div>
   </div>
   ```

---

## 3. Zero-Runtime и автономность на смартфоне

- Для работы локально на смартфонах без выхода в интернет запрещено подключать CDN-скрипты Tailwind Play.
- Стили компилируются один раз в монолитный CSS или встраиваются инлайн в `<style>` (размер до 6 КБ), обеспечивая мгновенный рендеринг за 1-2 миллисекунды.
