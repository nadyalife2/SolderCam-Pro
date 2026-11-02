# Проектные правила: OnePlus Nord N10 5G (SolderCam Pro & Battery Guard)

## 1. Специализация и фокус проекта
Данный репозиторий посвящен:
- Разработке Android-приложения `com.soldercam.pro` (Kotlin, Camera2 API, MediaRecorder, ViewBinding, Jetpack).
- Аппаратной и программной диагностике питания и аккумулятора OnePlus Nord N10 5G (`BE2029`, Snapdragon 690, контроллеры TI BQ27541 / PM7250B, термодатчики NTC).
- Настройке качества фото и алгоритмов сенсора OmniVision OV64B (HDR+, GCam-конфиги, Multi-frame RAW Stacking).
- Реверс-инжинирингу стоковых модулей камеры и системных библиотек Qualcomm Chromatix.
- UI/UX интерфейсу мобильного приложения и встроенного баг-трекера.

---

## 2. Разрешенные скилы для проекта
В рамках работы над данным проектом используются исключительно следующие профильные скилы:
- [`gadget-camera-tuning`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/gadget-camera-tuning/SKILL.md) — сенсоры камер, тюнинг OV64B, Camera2 API, алгоритмы HDR+, диагностика питания, PMIC и NTC-термисторов.
- [`mobile-android-design`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/mobile-android-design/SKILL.md) — мобильная эргономика, Material Design 3, touch targets, адаптивная верстка и удобство пользования.
- [`android-cli`](file:///C:/Users/MSI/.gemini/config/plugins/android-cli-plugin/skills/SKILL.md) — управление Android SDK, эмуляторами, сборкой и ADB-командами.
- [`reverse-engineer-anything`](file:///C:/Users/MSI/.gemini/config/skills/reverse-engineer-anything/SKILL.md) — реверс-инжиниринг APK, библиотек `.so` и байткода.
- [`impeccable`](file:///C:/Users/MSI/.gemini/config/skills/impeccable/SKILL.md) — дизайн и верстка мобильного интерфейса.
- [`melvin-edge-ai`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/melvin-edge-ai/SKILL.md) — автономный локальный ИИ-ассистент, Bionic + PRoot Alpine, нативный llama.cpp ARMv8, быстрый роутер инструментов, новости, таймеры и WebAudio.
- [`budget-tablet-unmasking-tuning`](file:///d:/для%20one%20plus%20nord%20n10/.agents/skills/budget-tablet-unmasking-tuning/SKILL.md) — снятие масок фейковых характеристик, формулы физической памяти, драйверы Fastboot MediaTek, не-рут деблоат, AOT-компиляция в speed mode и 1-кнопочный обход ТСПУ/DPI.
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

