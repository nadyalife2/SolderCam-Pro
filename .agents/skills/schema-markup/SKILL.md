---
name: schema-markup
description: Generates validated Schema.org JSON-LD structured data for TechArticle, SoftwareApplication, FAQPage, Organization, and Product. Use to earn Google Rich Snippets, Star Ratings in SERP, and high-confidence citation in AI answer engines (Perplexity, ChatGPT, Gemini).
version: 1.0.0
---

# Schema.org Structured Data Generator

Скил для генерации семантической микроразметки в формате JSON-LD.

## Поддерживаемые типы:
- **`SoftwareApplication`:** для мобильных приложений (`com.soldercam.pro`, APK-инструментов).
- **`TechArticle`:** для инженерных статей, гайдов по рутированию и кластерной документации.
- **`FAQPage`:** для секций вопросов и ответов на лендингах.
- **`Product`:** для оборудования, тепловизоров и плат.

## Генерация через Python:
```bash
python scripts/generate_schema_markup.py
```
Любая HTML-страница сайта или статья базы знаний обязана содержать блок `<script type="application/ld+json">` для индексации поисковыми роботами и GEO-движками.
