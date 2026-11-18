# Проектные правила: Triad-Omni Edge AI Cluster (Xiaomi Mi 10T, OnePlus Nord N10 5G, Redmi Note 4)

## 1. Специализация и фокус проекта
Данный репозиторий посвящен:
- Развертыванию гетерогенного автономного ИИ-кластера **Triad-Omni v4.7**:
  - **NODE-1 (Главный мозг):** Xiaomi Mi 10T 5G (`M2007J3SY`, `apollo`, Snapdragon 865, 8GB LPDDR5, LibreMobileOS 15) — LLM `Qwen3.5-9B-MTP` + `Gemma 4 E4B` @ `:8080`.
  - **NODE-2 (Рефлексы и векторная база):** OnePlus Nord N10 5G (`BE2029`, `billie`, Snapdragon 690, 6GB LPDDR4X, OxygenOS 11) — `LFM2.5-8B-A1B` @ `:8081` + `BGE-M3` @ `:8082` + TWRP + Battery Guard 24/7.
  - **NODE-3 (Шлюз телеметрии и хаб):** Xiaomi Redmi Note 4 (`mido`, Snapdragon 625) @ `:8000`.
- Аппаратной и системной оптимизации: Magisk root, A/B разметка, TWRP, отключение троттлинга, прямое питание без деградации батареи (sysfs `charging_enabled` / `input_suspend`).
- Разработке Android-приложения `com.soldercam.pro` (Kotlin, Camera2 API, NTC-телеметрия).

---

## 2. Железные обязательные правила (Выполнять ВСЕГДА БЕЗ НАПОМИНАНИЙ)
1. **Обязательная скриншот-фиксация каждого шага:**
   - На каждом этапе работы, прошивки, проверки загрузчика, тестов и запуска сервисов агент ОБЯЗАН делать скриншот реального экрана устройства через `adb exec-out screencap -p > screenshots/<name>.png` с понятным говорящим именем.
   - Никогда не ждать, пока пользователь напомнит про скриншоты.
2. **Строгий авторский голос («Моим голосом» по `USER_VOICE_STYLE_GUIDE.md`):**
   - Все ответы, технические отчеты, комментарии к коду и статьи в `ARTICLES/` агент ОБЯЗАН писать строго в авторском стиле: **женский род прошедшего времени** («прошила», «собрала», «раскопала», «протестировала», «проверила», «вывела»), живой энергичный темп, инженерная точность, разбор граблей и нулевая терпимость к канцеляриту и воде.
   - Никогда не ждать напоминаний о стиле.
3. **Синхронизация графа знаний (`graphify`):**
   - После изменения скриптов, конфигураций или добавления статей в `ARTICLES/` всегда обновлять граф знаний через `graphify update .`.

---

## 2. Разрешенные скилы для проекта
В рамках работы над данным проектом используются исключительно следующие профильные скилы:
- [`gadget-camera-tuning`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/gadget-camera-tuning/SKILL.md) — сенсоры камер, тюнинг OV64B, Camera2 API, алгоритмы HDR+, диагностика питания, PMIC и NTC-термисторов.
- [`mobile-android-design`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/mobile-android-design/SKILL.md) — мобильная эргономика, Material Design 3, touch targets, адаптивная верстка и удобство пользования.
- [`compose-multiplatform-patterns`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/compose-multiplatform-patterns/SKILL.md) — Jetpack Compose & CMP: оптимизация рекомпозиций, thumb zone, touch targets 48dp, Camera2 оверлеи.
- [`tailwind-patterns`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/tailwind-patterns/SKILL.md) — Tailwind v4 CSS-First токены, container queries, anti-slop HUD дашборды.
- [`seo-geo-optimizer`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/seo-geo-optimizer/SKILL.md) — технический SEO, Schema.org JSON-LD и Generative Engine Optimization под Perplexity/ChatGPT.
- [`product-growth-cro`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/product-growth-cro/SKILL.md) — RICE приоритизация, продающий копирайтинг лендингов, онбординг.
- [`schema-markup`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/schema-markup/SKILL.md) — микроразметка JSON-LD (SoftwareApplication, TechArticle, FAQPage).
- [`content-creator`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/content-creator/SKILL.md) — проверка авторского стиля brand_voice_analyzer.py и отсев воды.
- [`copywriting`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/copywriting/SKILL.md) — копирайтинг первого экрана, УТП, закрытие возражений.
- [`content-marketer`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/content-marketer/SKILL.md) — дистрибуция и переупаковка статей в Telegram/Habr/Reddit.
- [`programmatic-seo`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/programmatic-seo/SKILL.md) — масштабируемая генерация посадочных страниц по датасетам.
- [`product-manager`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/product-manager/SKILL.md) — PRD, Lean Canvas, скоринг фичей по формуле RICE.
- [`marketing-ideas`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/marketing-ideas/SKILL.md) — база из 140+ стратегий органического роста.
- [`ui-design-system`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/ui-design-system/SKILL.md) — дизайн-токены, кибердек-палитра, состояния компонентов.
- [`artifacts-builder`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/artifacts-builder/SKILL.md) — автономные интерактивные HTML/SVG виджеты.
- [`onboarding-cro`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/onboarding-cro/SKILL.md) — оптимизация первого опыта пользователя (AHA-момент < 60 с).
- [`android-cli`](file:///C:/Users/MSI/.gemini/config/plugins/android-cli-plugin/skills/SKILL.md) — управление Android SDK, эмуляторами, сборкой и ADB-командами.
- [`reverse-engineer-anything`](file:///C:/Users/MSI/.gemini/config/skills/reverse-engineer-anything/SKILL.md) — реверс-инжиниринг APK, библиотек `.so` и байткода.
- [`awesome-rea`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/awesome-rea/SKILL.md) — локальная офлайн-база знаний из 1265+ инструментов реверса, 442 кейсов и 235 научных статей по декомпиляции.
- [`rea-analysis-optimization`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/rea-analysis-optimization/SKILL.md), [`rea-tool-design`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/rea-tool-design/SKILL.md) — расширенный инструментарий REA.
- [`impeccable`](file:///C:/Users/MSI/.gemini/config/skills/impeccable/SKILL.md) — дизайн и верстка мобильного интерфейса.
- [`melvin-edge-ai`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/melvin-edge-ai/SKILL.md) — автономный локальный ИИ-ассистент, Bionic + PRoot Alpine, нативный llama.cpp ARMv8, быстрый роутер инструментов, новости, таймеры и WebAudio.
- [`budget-tablet-unmasking-tuning`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/budget-tablet-unmasking-tuning/SKILL.md) — снятие масок фейковых характеристик, формулы физической памяти, драйверы Fastboot MediaTek, не-рут деблоат, AOT-компиляция в speed mode и 1-кнопочный обход ТСПУ/DPI.
- [`tochka-plavleniya-pipeline`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/tochka-plavleniya-pipeline/SKILL.md) — автономный SaaS-конвейер полного цикла: бриф, 2 авторских голоса (Practico 1 инженер и Practico 2 заказчик), Markdown-парсер, валидация по схеме v1.1, скоринг ОТК, безопасная доставка через `delivery_cli.py` и разметка Schema.org.
- [graphify](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/graphify/SKILL.md) — построение и опрос графа знаний архитектуры кодовой базы, god-ноды, кластеризация и BFS/DFS-трассировка.
- Базовые системные скилы Antigravity ([`antigravity-guide`](file:///C:/Users/MSI/.gemini/antigravity/builtin/skills/antigravity_guide/SKILL.md), [`automation`](file:///C:/Users/MSI/.gemini/antigravity/builtin/skills/automation/SKILL.md), [`generative_ui`](file:///C:/Users/MSI/.gemini/antigravity/builtin/skills/generative_ui/SKILL.md), [`agy-customizations`](file:///C:/Users/MSI/.gemini/antigravity/builtin/skills/agy-customizations/SKILL.md)).

---

## 3. Исключенные (игнорируемые) скилы
Для данного проекта строго **запрещено** активировать, подключать или использовать сторонние глобальные скилы:
- ❌ Все научные, химические и биомедицинские скилы плагина `science` (AlphaFold, UniProt, PubMed, ChEMBL, PDB, BLAST, Foldseek, геномика, мутации и т.д.).
- ❌ Серверные облачные скилы `google-cloud-developer` (GCP, GKE, IAM).
- ❌ Непрофильные темы ([`palmistry-chirology`](file:///C:/Users/MSI/.gemini/config/skills/palmistry-chirology/SKILL.md)).

Агент должен фокусироваться только на коде проекта, Android-архитектуре, аппаратной части смартфона и алгоритмах обработки изображения.

---

## 4. Авторский стиль и голос публикаций
При подготовке любых статей, гайдов, отчетов или постов от лица автора агент обязан руководствоваться профилем авторского стиля:
- [`USER_VOICE_STYLE_GUIDE.md`](file:///d:/для%20one%20plus%20nord%20n10/USER_VOICE_STYLE_GUIDE.md) — живой диалог, женский род прошедшего времени, инженерная конкретика, разбор фейлов и граблей, нулевая терпимость к «воде».

---

## 5. Обязательная скриншот-фиксация для статей и отчетов
На каждом этапе работы, отладки, восстановления, оптимизации и тестирования агент ОБЯЗАН:
- Фиксировать ключевые состояния реального экрана устройства через `adb screencap` (бутскрин, локскрин, рабочий стол, системные настройки, логи ошибок, интерфейс ассистента и доказательства стабильности).
- Сохранять скриншоты в папку артефактов/скриншотов проекта с понятными говорящими именами.
- Использовать эти скриншоты как доказательную базу и иллюстрации для будущих инженерных статей и документации.

---

## 6. Непрерывное ведение заметок и статей «Моим голосом»
Для каждого нового этапа, архитектурного расширения, интеграции или сетевого взаимодействия агент ОБЯЗАН:
- Фиксировать инженерный лог и практические выводы в формате заметок для статей.
- Строго соблюдать профиль [`USER_VOICE_STYLE_GUIDE.md`](file:///d:/для%20one%20plus%20nord%20n10/USER_VOICE_STYLE_GUIDE.md): женский род прошедшего времени («собрала», «раскопала», «протестировала»), живой темп, юмор, предельная инженерная точность, без канцеляризмов и «воды».
- Своевременно дополнять и расширять цикл статей в директории `ARTICLES/` новым материалом.

