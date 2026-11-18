# 🔬 Инженерное руководство по Reverse Engineering Anything (REA) и декомпиляции

> **Статус документа:** Эталонная база знаний по реверс-инжинирингу для кластера Triad-Omni и портала «Точка Плавления».  
> **Инструментарий:** 255 MCP инструментов REA, Ghidra, JADX, Frida, Rizin, IDA Pro, Binwalk, TShark, `inspect_model_artifact`, каталог Awesome-REA (1265+ инструментов).

---

## 1. Архитектура REA и профили анализа

Reverse Engineer Anything (REA v6.9.0) — это многодоменный фреймворк статического и динамического анализа, разделенный по типам исследуемых целей (Targets):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        РЕВЕРС-АРХИТЕКТУРА REA                          │
└───────┬───────────────────────────────┬────────────────────────┬───────┘
        │                               │                        │
┌───────▼───────────────┐       ┌───────▼──────────────┐ ┌───────▼──────┐
│     Android & DEX     │       │    Native Binaries   │ │   AI & Models│
│ JADX, inspect_apk,    │       │ Ghidra, IDA, Rizin,  │ │ inspect_model│
│ Frida, Chromatix ISP  │       │ ELF/PE hardening     │ │ GGUF, tensors│
└───────────────────────┘       └──────────────────────┘ └──────────────┘
```

---

## 2. Реверс Android APK, DEX и нативных библиотек (.so)

### 2.1. Исследование APK и распаковка
* **Инструмент REA:** `inspect_android_package`, `inspect_apk_signature`.
* **Процедура анализа:**
  1. Проверка сигнатуры APK (`v1 JAR, v2, v3, v3.1`) и SHA-256 сертификата разработчика.
  2. Извлечение манифеста `AndroidManifest.xml`: поиск экспортированных Activity, Service, BroadcastReceiver (`android:exported="true"`), кастомных разрешений и флагов отладки (`android:debuggable`).
  3. Декомпиляция DEX-байткода в Java через JADX (`jadx -d out/ target.apk`).
  4. Анализ обфускации: ProGuard / R8 (переименование классов в `a.b.c`), DexGuard / SecShell / Bangcle (шифрование строк, динамическая подгрузка dex).

### 2.2. Нативные библиотеки (.so) под архитектуру ARM64-v8a
* В Android-приложениях с интенсивной графикой, нейросетями или криптографией критическая логика компилируется в `lib/<arch>/lib*.so`.
* **Декомпиляция через REA:** `open_binary` с указанием пути к `.so` $\to$ `analyze_function` $\to$ `procedure_pseudo_code`.
* **Qualcomm Chromatix ISP:** В нашем проекте `com.soldercam.pro` реверс библиотек камеры Qualcomm (`libmmcamera_*.so`, `libchromatix_*.so`) позволил снять аппаратные лимиты сенсора OV64B на OnePlus Nord N10:
  * Включение ручной экспозиции до 30 секунд;
  * Чтение RAW10 байеровских фреймов без артефактов шумоподавления;
  * Прямой опрос регистров термодатчиков NTC через драйвер ядра `/sys/class/thermal/thermal_zone*`.

---

## 3. Реверс нативных бинарников (ELF / PE / Mach-O)

### 3.1. Анализ защиты бинарника (Binary Hardening)
Перед глубоким дизассемблированием запускается `inspect_binary_hardening`:
* **PIE (Position Independent Executable):** Рандомизация адресного пространства (ASLR).
* **Stack Canary (fstack-protector):** Защита от переполнения стека.
* **RELRO (Relocation Read-Only):** Полный (Full) или частичный (Partial) запрет перезаписи таблицы GOT (Global Offset Table).
* **NX / DEP (No-Execute):** Запрет исполнения кода в стеке и куче.

### 3.2. Статический анализ через Ghidra и Kuna
* Поиск перекрестных ссылок: `xrefs` на критические строковые литералы (API ключи, системные вызовы, шифрованные заголовки).
* Вычисление графа вызовов: `get_call_graph` для восстановления логики авторизации и шифрования.
* Проверка таблиц импорта: `inspect_pe_imports` и `inspect_native_exports`.

---

## 4. Динамическая инструментация через Frida

При анализе защищенных приложений статический анализ дополняется динамическим перехватом функций в памяти:
```javascript
// Перехват криптографических вызовов и обход SSL Pinning
Java.perform(function () {
    var CertificatePinner = Java.use("okhttp3.CertificatePinner");
    CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function (str, list) {
        console.log("[+] SSL Pinning bypassed for: " + str);
        return; // Возвращаем пустоту без исключения
    };
});
```

---

## 5. Инспекция ИИ-моделей GGUF и Safetensors

REA v6.9.0 содержит специализированный инструмент `inspect_model_artifact`:
* **Формат GGUF (llama.cpp):**
  * Чтение метаданных: архитектура базовой модели (`qwen2`, `llama`, `phi3`), размер контекста (`context_length`), размер словаря (`vocab_size`), тип квантования (`q4_k_m`, `iq3_xxs`, `ud-q3_k_xl`).
  * Проверка целостности тензоров: расчет SHA-256 весов без полной загрузки 5 ГБ в оперативную память.
  * Анализ слоев LoRA: инспекция ранга $r$ и коэффициента масштабирования $\alpha$ в сменных картриджах `adapter.gguf`.

---

## 6. Реверс прошивок и IoT оборудования пайки

При исследовании паяльных станций (TS100, TS80P, Pinecil, JBC, T12):
1. **Дамп памяти микроконтроллера:** Снятие прошивки через SWD/JTAG (STM32, GD32, CH32V, ESP32) с помощью OpenOCD.
2. **Распаковка образов:** `inspect_firmware_regions` и `extract_firmware` через Binwalk / Unblob.
3. **Восстановление алгоритма PID-регулятора:** Дизассемблирование модуля управления нагревателем жала (ШИМ-скважность, калибровка АЦП термопары по коэффициенту Зеебека).
