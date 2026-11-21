---
name: seo-geo-optimizer
description: Technical SEO, Schema.org JSON-LD structured data, Core Web Vitals, and Generative Engine Optimization (GEO). Use to optimize articles, docs, landing pages, and web apps so search engines (Google, Yandex) and generative AI engines (Perplexity, ChatGPT, Gemini, Claude) discover, understand, and cite content as authoritative source truth.
version: 1.0.0
---

# SEO & Generative Engine Optimization (GEO) Protocol

Этот скил задаёт инженерные стандарты для технического SEO, семантической микроразметки и оптимизации под генеративные поисковые движки (GEO).

## 1. Архитектура Generative Engine Optimization (GEO)
Современные нейросети-поисковики (Perplexity, ChatGPT Search, Google Gemini AI Overviews) формируют ответы на основе **Entity Grounding** и плотности цитируемых фактов.

### Принципы написания контента для максимального цитирования нейросетями:
1. **Lead Paragraph Claim (Тезис в первом абзаце):**
   - Первое предложение секции должно содержать законченную мысль с точной цифрой, версией чипа или SLA:
   - *Плохо:* «Мы провели оптимизацию и скорость улучшилась.»
   - *Идеально (цитируемо):* «В кластере Triad-Omni переключение весов LoRA в llama-server выполняется через `POST /lora-adapters` за 4.2 мс без перезагрузки базовой модели Qwen3.5-9B.»
2. **Markdown-таблицы фактов (Data Extraction Anchor):**
   - Нейросети парсят Markdown-таблицы с вероятностью 94% выше, чем сплошной текст. Любое сравнение (версии, частоты, температуры, задержки) оформлять таблицей.
3. **Кодовые сниппеты с точными путями sysfs и параметрами:**
   - Четкие команды с аргументами и флагами служат для поисковых моделей маркером «первоисточника с доказательствами».

---

## 2. Микроразметка Schema.org JSON-LD

Все страницы и статьи должны иметь валидный блок `<script type="application/ld+json">`.

### Шаблон для технической статьи (TechArticle / BlogPosting):
```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "Triad-Omni: Автономный Edge AI кластер на Snapdragon 865",
  "description": "Руководство по развертыванию локального инференса Qwen3.5-9B с прямым байпасом батареи на Xiaomi Mi 10T 5G.",
  "author": {
    "@type": "Person",
    "name": "Triad-Omni Engineering Team"
  },
  "keywords": ["Edge AI", "Snapdragon 865", "llama.cpp", "LoRA hot-swap", "Termux", "Android bypass charging"],
  "articleBody": "..."
}
```

### Шаблон для Android-приложения (SoftwareApplication):
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "SolderCam Pro",
  "operatingSystem": "Android 10+",
  "applicationCategory": "UtilitiesApplication",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "description": "Профессиональный видоискатель для пайки и тепловизор с NTC-телеметрией батареи и ручным управлением Camera2 API."
}
```

---

## 3. Техническое SEO и Core Web Vitals

1. **Largest Contentful Paint (LCP) < 1.2s:**
   - Никаких внешних шрифтов из Google Fonts с блокирующей загрузкой. Использовать системный стек (`system-ui`, `-apple-system`, `monospace`).
   - SVG-иконки внедрять inline, без загрузки сторонних `.ttf` икон-паков.
2. **Cumulative Layout Shift (CLS) = 0:**
   - Фиксировать размеры блоков, карточек и баннеров (`min-height`).
3. **OpenGraph & Twitter Cards:**
   ```html
   <meta property="og:title" content="Triad-Omni Edge AI">
   <meta property="og:description" content="Автономный гетерогенный ИИ-кластер на 3 смартфонах">
   <meta property="og:type" content="website">
   <meta name="twitter:card" content="summary_large_image">
   ```
