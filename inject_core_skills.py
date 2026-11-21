# -*- coding: utf-8 -*-
import os, sys

target_file = 'd:/для one plus nord n10/omni_gateway.py'
with open(target_file, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. CORE_STARTER_SKILLS блок
skills_code = '''
# =====================================================================
# ВШИТЫЙ ПАКЕТ СТАРТОВЫХ ИНЖЕНЕРНЫХ НАВЫКОВ (CORE STARTER SKILLS v4.0)
# =====================================================================
CORE_STARTER_SKILLS = [
    (
        "reva_android",
        "Ghidra_ReVa_JNI_Bridge_Reconstruction",
        "СТАНДАРТ АНАЛИЗА ANDROID JNI В GHIDRA (ReVa): "
        "1) Первый аргумент любой JNI-функции (регистр X0 на ARM64) всегда типизируй как JNIEnv*, второй (X1) — как jobject thiz или jclass. "
        "2) При анализе JNI_OnLoad находи вызовы (*env)->RegisterNatives (смещение +0x6b8 в таблице JNINativeInterface на 64-битных системах) и восстанавливай массив структур JNINativeMethod {char* name, char* signature, void* fnPtr}. "
        "3) Всегда сопоставляй дескрипторы типов JNI (например, '(Ljava/lang/String;I)Z') с конкретными типами C/C++ и переименовывай функции в формат Java_<Class>_<Method>."
    ),
    (
        "reva_android",
        "ARM64_ABI_And_Struct_Recovery",
        "СТАНДАРТ ВОССТАНОВЛЕНИЯ СТРУКТУР C/C++ И ABI AARCH64: "
        "1) Учитывай стандарт AAPCS64: X0-X7 передают целочисленные аргументы и указатели, X8 — адрес буфера для возврата крупной структуры по значению, D0-D7 — числа с плавающей точкой. "
        "2) Если в декомпилированном коде Ghidra видны обращения вида *(int *)(param_1 + 0x10), *(long *)(param_1 + 0x18), не оставляй сырую адресную арифметику — сформируй определение C-структуры с выравниванием полей по границам 4/8 байт. "
        "3) Для C++ объектов первыми 8 байтами (смещение 0x00) всегда проверяй наличие указателя на таблицу виртуальных методов (vtable**)."
    ),
    (
        "reva_android",
        "Control_Flow_Deobfuscation_Analysis",
        "АНАЛИЗ СЛОЖНЫХ ГРАФОВ УПРАВЛЕНИЯ (CFG) И ДЕКОМПИЛЯЦИЯ: "
        "1) Если функция содержит бесконечный цикл while(true) с переменной состояния (state variable) и большим switch — это уплощение потока управления (Control Flow Flattening). Выдели начальное состояние, конечные блоки выхода и построй прямую последовательность вызовов без диспетчера. "
        "2) Заменяй константные побитовые выражения и избыточные арифметические тождества (MBA) эквивалентными простыми операциями C. "
        "3) В отчете всегда указывай точные адреса базовых блоков и назначение восстановленной функции."
    ),
    (
        "esp32",
        "ESP32_FreeRTOS_DMA_Hardware_Architecture",
        "СТАНДАРТ РАЗРАБОТКИ ПРОШИВОК ESP32 / ESP32-S3 (ESP-IDF & FreeRTOS): "
        "1) Жестко разделяй ядра: на Core 0 (PRO_CPU) оставляй стек Wi-Fi, Bluetooth и сетевые сокеты; все задачи реального времени (чтение I2S микрофона INMP441, вывод звука MAX98357A, опрос датчиков и камеры OV3660) привязывай к Core 1 (APP_CPU) через xTaskCreatePinnedToCore. "
        "2) Обработчики прерываний GPIO/таймеров помечай атрибутом IRAM_ATTR и используй внутри только FreeRTOS API с суффиксом FromISR (xQueueSendFromISR). "
        "3) Для потокового аудио и буферов камеры используй DMA-совместимую память: heap_caps_malloc(size, MALLOC_CAP_DMA) или PSRAM (MALLOC_CAP_SPIRAM) с проверкой выравнивания."
    ),
    (
        "solder",
        "Solder_Metallurgy_GOST_IPC_Practico",
        "СТАНДАРТ МЕТАЛЛУРГИИ ПАЙКИ И ВИЗУАЛЬНОЙ ИНСПЕКЦИИ ПЛАТ (ГОСТ / IPC): "
        "1) Всегда сверяй температуры плавления: ПОС-61 (ГОСТ 21930-76) — солидус 183°C, ликвидус 190°C, рабочая на жале 235–250°C; бессвинцовый SAC305 (Sn96.5Ag3.0Cu0.5) — плавление 217–220°C, рабочая на жале 260–285°C. "
        "2) Флюсы классифицируй строго по IPC J-STD-004B (ROL0, ROM1, ORH1) с указанием необходимости отмывки и коррозионной активности галогенидов. "
        "3) При анализе фото печатной платы через модуль зрения (mmproj) оценивай угол смачивания галтели припоя, наличие холодной пайки, перегрева маски, шариков припоя (solder balls) и перемычек на выводах SMD/QFN/BGA according to IPC-A-610."
    ),
    (
        "ui_video",
        "HTMLmark_2.0_Industrial_Workbench_UI",
        "СТАНДАРТ ГЕНЕРАЦИИ ИНТЕРФЕЙСОВ И ВИДЕО (HTMLmark 2.0 Industrial Theme): "
        "1) Никаких шаблонных фиолетово-розовых градиентов. Используй палитру 'Инженерный Верстак': фон #0b1120, панель #161f33, границы 1px solid #263554, акцент нагрева #f59e0b, технический #38bdf8, успех #22c55e. "
        "2) Все интерактивные инженерные калькуляторы верстай на адаптивном CSS Grid (корректное отображение от 320px на мобильных без горизонтального скролла) и чистом Vanilla JS с мгновенным пересчетом значений при движении ползунков. "
        "3) При генерации скриптов Manim используй темный фон #0f172a, четкие засечки осей и контрастные подписи без наложения текста."
    )
]

for dom, top, cont in CORE_STARTER_SKILLS:
    conn.execute("""
        INSERT OR IGNORE INTO skills_meta(domain, topic, content, source_folder, utility_score, updated_at)
        VALUES (?, ?, ?, 'Built-in Core v4.0', 10, ?)
    """, (dom, top, cont, datetime.now().strftime("%Y-%m-%d %H:%M")))
conn.commit()
'''

# 2. Легковесный модуль Web-поиска (DuckDuckGo Lite)
web_search_code = '''
# ----------------- ЛЕГКОВЕСНЫЙ ВЕБ-ПОИСК (DUCKDUCKGO LITE) -----------------
def web_search_ddg(query, max_results=3):
    """Ищет в интернете без API-ключей, вытаскивая чистые сниппеты для промпта"""
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        
        results = []
        # Простой парсинг сниппетов
        import re
        snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
        titles = re.findall(r'<a class="result__url[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
        for i in range(min(max_results, len(snippets))):
            clean_s = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            clean_t = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else "Web"
            if clean_s:
                results.append(f"[{clean_t}]: {clean_s}")
        return "\\n".join(results)
    except Exception as e:
        return ""
'''

if 'CORE_STARTER_SKILLS =' not in code:
    marker = 'conn.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, level TEXT, msg TEXT);")\nconn.commit()'
    code = code.replace(marker, marker + '\n' + skills_code + '\n' + web_search_code)
    print("Injected CORE_STARTER_SKILLS & web_search_ddg successfully!")

# 3. Добавляем веб-поиск в роутер промптов (/v1/chat/completions)
if 'web_search_ddg' in code and 'web_info =' not in code:
    router_target = '            kb_text = get_kb_context(domain, last_prompt)'
    router_replacement = '''            kb_text = get_kb_context(domain, last_prompt)

            # Проверка intent на поиск в интернете
            web_info = ""
            if any(w in last_prompt.lower() for w in ["найди в сети", "поищи в интернете", "что пишут", "свежие новости", "datasheet", "распиновка", "4pda", "github"]):
                add_log(f"Запуск веб-поиска для запроса: '{last_prompt[:50]}'")
                web_info = web_search_ddg(last_prompt)'''
    code = code.replace(router_target, router_replacement)
    
    msg_target = '            if kb_text:\n                sys_msg = f"ФАКТЫ ИЗ БАЗЫ ЗНАНИЙ (FTS5):\\n{kb_text}"\n                enriched_msgs.insert(0, {"role": "system", "content": sys_msg})'
    msg_replacement = '''            if kb_text or web_info:
                facts = []
                if kb_text:
                    facts.append(f"ФАКТЫ ИЗ БАЗЫ ЗНАНИЙ (FTS5):\\n{kb_text}")
                if web_info:
                    facts.append(f"СВЕЖИЕ ДАННЫЕ ИЗ СЕТИ INTERNET (DuckDuckGo):\\n{web_info}")
                sys_msg = "\\n\\n".join(facts)
                enriched_msgs.insert(0, {"role": "system", "content": sys_msg})'''
    code = code.replace(msg_target, msg_replacement)
    print("Injected Web Search prompt enrichment successfully!")

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved updated omni_gateway.py")
