"""Скрипт компиляции обучающего датасета Tochka-Plavleniya для агента Triad-Omni."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP_DIR = Path(r"D:\tochka-plavleniya")
ARTICLES_DIR = TP_DIR / "сами статьи"
DATASETS_DIR = ROOT / "datasets"
SFT_TARGET = DATASETS_DIR / "triad_omni_sft_dataset.jsonl"
TP_STANDALONE = DATASETS_DIR / "tochka_plavleniya_sft.jsonl"

SYSTEM_PROMPT = (
    "Ты — бортовой инженер и координатор гетерогенного автономного кластера Triad-Omni "
    "(Xiaomi Mi 10T 5G, OnePlus Nord N10 5G, Redmi Note 4), а также оператор автономного "
    "контентного SaaS-конвейера проекта «Точка Плавления». Отвечай технически строго, "
    "в авторском стиле создательницы кластера (женский род прошедшего времени: проверила, "
    "раскопала, прошила, замерила, упаковала), с точными путями к скриптам, флагами запуска, "
    "схемами контрактов v1.1, физическими сплавами и без корпоративной воды."
)

articles_map = [
    {
        "file": "1-kak-payat-payalnikom-poshagovyj-gajd-dlya-nachinayushchih.md",
        "title": "Как правильно паять паяльником с нуля",
        "voice": "practico",
        "topic": "Пошаговый регламент пайки паяльником для начинающих: физика смачивания, подготовка жала, флюсы и режимы",
    },
    {
        "file": "2-s-chego-nachat-payku-startovyj-nabor.md",
        "title": "С чего начать пайку: стартовый набор инструмента",
        "voice": "practico2",
        "topic": "Стартовый набор для монтажа электроники: необходимый минимум, смета, где не переплачивать за маркетинг",
    },
    {
        "file": "3-payka-provodov-kak-pravilno-soedinit-i-izolirovat.md",
        "title": "Пайка проводов: скрутка, обжим или пайка",
        "voice": "practico",
        "topic": "Технологический регламент соединения медных проводов: капиллярный затек, теплоотвод и деградация изоляции",
    },
    {
        "file": "4-kak-nauchitsya-payat-bystro-i-bez-braka.md",
        "title": "Как научиться паять быстро и без брака",
        "voice": "practico",
        "topic": "Методика постановки руки монтажника: мышечная память, контроль пятна контакта и визуальные критерии ГОСТ",
    },
    {
        "file": "6-kakoj-payalnik-vybrat.md",
        "title": "Какой паяльник выбрать: нихром, керамика или картриджи T12/C245",
        "voice": "practico2",
        "topic": "Выбор паяльника для домашней мастерской: реальная теплоемкость, скорость нагрева и цена одного часа работы",
    },
    {
        "file": "15-pripoj-dlya-pajki-vidy.md",
        "title": "Припои для пайки: классификация и выбор сплава",
        "voice": "practico",
        "topic": "Классификация припоев: оловянно-свинцовые, бессвинцовые, эвтектика, диаграммы фазового равновесия",
    },
    {
        "file": "16-pos-61-i-pos-40-raznica.md",
        "title": "ПОС-61 против ПОС-40: разница сплавов и температурный интервал",
        "voice": "practico",
        "topic": "Сравнение ПОС-61 и ПОС-40: интервал кристаллизации, кашеобразная фаза и риск холодной пайки",
    },
    {
        "file": "17-bessvincovyj-pripoj.md",
        "title": "Бессвинцовая пайка: сплавы SAC305 и SN100C",
        "voice": "practico",
        "topic": "Особенности бессвинцового монтажа: деградация жал, флюсовая активность и термопрофили пайки",
    },
    {
        "file": "25-oshibki-novichka-pri-pajke.md",
        "title": "5 типичных ошибок новичка при пайке",
        "voice": "practico",
        "topic": "Типичные ошибки при ручном монтаже: холодная пайка, перегрев печатных проводников, избыток припоя",
    },
    {
        "file": "52-payalnaya-pasta-ili-pripoj.md",
        "title": "Паяльная паста против трубчатого припоя",
        "voice": "practico2",
        "topic": "Что выбрать для SMD-монтажа: паяльная паста в шприце или проволочный припой с флюсом",
    },
]

sop_pairs = [
    {
        "q": "Как устроен полный цикл публикации статьи в «Точке Плавления» через CLI?",
        "a": (
            "Я отладила конвейер так, чтобы он работал без единой ручной операции:\n\n"
            "1. `seo.db` отдает тему, слаг и связи перелинковки.\n"
            "2. `writer_practico.py --id <ID> --voice <practico|practico2> --provider deepseek` "
            "генерирует черновик (себестоимость 6 копеек за 7 000 знаков).\n"
            "3. `package_contract.py` очищает frontmatter, парсит таблицы Markdown в `<table>`, "
            "вырезает блок `### FAQ:` во избежание дублирования и нормализует оснастку.\n"
            "4. `score_article.py` локально скорит текст (проходной балл >= 80).\n"
            "5. Пакет валидируется по `schemas/article-contract-v1.1.schema.json` (сплавы 11 шт. или 'none').\n"
            "6. `python tools/delivery_cli.py send-draft --package <JSON>` отправляет пост в WordPress в статусе draft "
            "с контрольной побайтовой сверкой метаполей через REST API.\n"
            "7. В WordPress тема `theme4` выводит мобильный паспорт техпроцесса, источники и обогащает Rank Math "
            "сущностью `@type: FAQPage`."
        ),
    },
    {
        "q": "В чем ключевая разница между голосами Practico 1 и Practico 2?",
        "a": (
            "Разница не в теме, а в точке зрения:\n\n"
            "• **Practico 1 (Инженер):** смотрит на физику процесса. Вопрос: «почему так происходит». "
            "Формула абзаца: Факт -> Физический механизм -> Практическое последствие. Термины: солидус, "
            "ликвидус, эвтектика, ГОСТ 21931-76, IPC-A-610. Сухая инженерная ирония.\n\n"
            "• **Practico 2 (Заказчик / владелец мастерской):** смотрит на смету и время. Вопрос: «сколько это стоит "
            "и что мне делать». Формула абзаца: Что делать -> Цена/время -> Цена ошибки. Рубленый синтаксис (15–18 слов), "
            "короткие абзацы: «Это дорого. Это не нужно. Это работает». Ирония над маркетингом и переплатами."
        ),
    },
    {
        "q": "Как валидировать статью по схеме article-contract-v1.1.schema.json, если в ней нет пайки и припоя?",
        "a": (
            "Я сняла жесткую блокировку в схеме v1.1:\n"
            "1. Поле `solder_alloy` теперь поддерживает каноническое значение `'none'` (помимо 10 марок припоев).\n"
            "2. Поле `temp_data` может принимать значение `null` (или отсутствовать).\n"
            "3. Поля `solder_alloy` и `temp_data` исключены из массива `required`.\n"
            "Теперь статьи по термофенам, микроскопам, химии и организации монтажного стола валидируются "
            "со 100% успехом без необходимости галлюцинировать температуру."
        ),
    },
]

def main():
    new_samples = []

    # 1. Добавляем статьи в датасет
    for item in articles_map:
        fpath = ARTICLES_DIR / item["file"]
        if not fpath.exists():
            continue
        content = fpath.read_text(encoding="utf-8").strip()
        # Чистим frontmatter если есть
        content_clean = re.sub(r"^---\n.*?\n---\n+", "", content, flags=re.DOTALL)
        
        user_prompt = (
            f"Напиши полную техническую статью для проекта «Точка Плавления» по теме: «{item['title']}».\n"
            f"Техническое задание: {item['topic']}.\n"
            f"Авторский голос: {'Practico 1 (Инженер-технолог)' if item['voice'] == 'practico' else 'Practico 2 (Владелец мастерской / Заказчик)'}."
        )

        sample = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": content_clean},
            ]
        }
        new_samples.append(sample)

    # 2. Добавляем SOP-пары
    for sop in sop_pairs:
        sample = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": sop["q"]},
                {"role": "assistant", "content": sop["a"]},
            ]
        }
        new_samples.append(sample)

    # 3. Сохраняем отдельный автономный датасет
    with TP_STANDALONE.open("w", encoding="utf-8") as f:
        for s in new_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"✅ Создан отдельный датасет {TP_STANDALONE}: {len(new_samples)} сэмплов.")

    # 4. Добавляем в основной sft датасет кластера
    with SFT_TARGET.open("a", encoding="utf-8") as f:
        for s in new_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"✅ Добавлено {len(new_samples)} сэмплов в {SFT_TARGET}.")

if __name__ == "__main__":
    main()
