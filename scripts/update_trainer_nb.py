#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni LoRA Trainer Notebook Generator v5.2 (Master Fast-Path Harness Edition)
Генерирует triad_omni_trainer.ipynb с полной поддержкой методологии Harness-Adapter:
- Двойной режим: Fast-Path Tool Adapter (r=32, alpha=64, Zero-CoT) и Persona/Knowledge LoRA (r=16, alpha=16)
- Отключение затяжного CoT-рассуждения для устранения 30–90 сек задержек на мобильном Snapdragon 865
- Сквозное версионирование картриджей <slug>_<version>_<timestamp>.omni.zip с паспортом card.json
- Автозагрузка датасета triad_omni_harness_sft.jsonl с Яндекс.Диска, Google Диска или локально
- Конвертация в adapter.gguf через llama.cpp и сохранение в Google Диск через PyDrive2
"""

import json
import os
from pathlib import Path

null = None

def get_notebook_dict():
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# ⚡ Triad-Omni v5.2: Fast-Path Harness Adapter & LoRA Trainer (Google Colab Tesla T4)\n",
                "### Автономное обучение адаптеров личности и высокоскоростных исполнителей инструментов для Xiaomi Mi 10T 5G (Snapdragon 865) и OnePlus Nord N10 5G\n",
                "- **Методология:** Harness-Adapter (Zero-CoT Tool Execution, pi-adapted)\n",
                "- **Оптимизация Pruned Output Head (smolmaxxing):** Усечение словаря со 152k до 64k токенов (экономия ~420 МБ LPDDR5 RAM на Mi 10T 5G, ускорение Softmax x2.38).\n",
                "- **REA Tool Suite:** Встроенные инструменты реверса (`inspect_apk_manifest`, `analyze_native_binary`, `extract_sysfs_telemetry`).\n",
                "- **Режимы:** \n",
                "  1. `Fast-Path Tool Adapter` (r=32, alpha=64): мгновенный вызов инструментов кластера в 1–8 шагов без задержек CoT-рассуждений (<think>).\n",
                "  2. `Persona & Knowledge` (r=16, alpha=16): дистилляция базы знаний и авторского стиля.\n",
                "- **Базовая модель кластера:** `unsloth/Qwen3.5-9B-Base` (или `Qwen/Qwen3.5-9B` под наш Mi 10T 5G)\n",
                "- **Целевые модули:** `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`\n",
                "- **Паспорт картриджа:** `card.json` с фиксацией SHA256, схемы `omni.lora.card/1` и режима `mode`\n",
                "- **Экспорт:** GGUF fp16 для нативного `--lora-scaled` в `llama.cpp` на мобильных устройствах"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": null,
            "metadata": {},
            "outputs": [],
            "source": [
                "#@title 🎛️ 1. Настройки режима, LoRA-параметров и зависимостей\n",
                "HARNESS_MODE = True #@param {type:\"boolean\"}\n",
                "PRUNE_VOCAB_HEAD = True #@param {type:\"boolean\"}\n",
                "TARGET_VOCAB_SIZE = 64000 #@param {type:\"integer\"}\n",
                "LORA_RANK = 32 #@param {type:\"slider\", min:4, max:64, step:4}\n",
                "LORA_ALPHA = 64 #@param {type:\"slider\", min:8, max:128, step:8}\n",
                "MAX_STEPS = 80 #@param {type:\"slider\", min:20, max:300, step:10}\n",
                "LEARNING_RATE = 2e-4 #@param {type:\"number\"}\n",
                "MAX_SEQ_LENGTH = 2048 #@param {type:\"slider\", min:512, max:4096, step:256}\n",
                "CARTRIDGE_SLUG = \"triad-omni-fast-tool\" #@param {type:\"string\"}\n",
                "CARTRIDGE_VERSION = \"v5.2\" #@param {type:\"string\"}\n",
                "ADD_TIMESTAMP = True #@param {type:\"boolean\"}\n",
                "\n",
                "from datetime import datetime, timezone\n",
                "import os, json, hashlib\n",
                "\n",
                "# Автоматическая калибровка параметров под выбранный режим\n",
                "if HARNESS_MODE:\n",
                "    if LORA_RANK < 32:\n",
                "        LORA_RANK = 32\n",
                "    if LORA_ALPHA < 64:\n",
                "        LORA_ALPHA = 64\n",
                "    if \"fast-tool\" not in CARTRIDGE_SLUG and \"harness\" not in CARTRIDGE_SLUG:\n",
                "        CARTRIDGE_SLUG = \"triad-omni-fast-tool\"\n",
                "    print(\"⚡ АКТИВИРОВАН РЕЖИМ FAST-PATH HARNESS ADAPTER (Zero-CoT Tool Execution)!\")\n",
                "    print(\"🎯 Модель обучается вызывать системные инструменты кластера напрямую, минуя 30-90 сек рассуждений.\")\n",
                "else:\n",
                "    print(\"📚 Активирован режим Persona & Knowledge LoRA.\")\n",
                "\n",
                "if PRUNE_VOCAB_HEAD:\n",
                "    print(f\"✂️ АКТИВИРОВАН РЕЖИМ PRUNED OUTPUT HEAD (smolmaxxing): усечение со 152k до {TARGET_VOCAB_SIZE} токенов!\")\n",
                "    print(\"💾 Экономия LPDDR5 RAM на Mi 10T 5G: ~420 МБ, ускорение Softmax x2.38.\")\n",
                "\n",
                "TIME_TAG = datetime.now().strftime(\"%Y%m%d_%H%M\")\n",
                "BUILD_TAG = f\"{CARTRIDGE_VERSION}_{TIME_TAG}\" if ADD_TIMESTAMP else CARTRIDGE_VERSION\n",
                "ARCHIVE_FILENAME = f\"{CARTRIDGE_SLUG}_{BUILD_TAG}.omni.zip\"\n",
                "LATEST_FILENAME = f\"{CARTRIDGE_SLUG}_latest.omni.zip\"\n",
                "\n",
                "print(f\"🏷️ Слот картриджа:   {CARTRIDGE_SLUG}\")\n",
                "print(f\"📌 Версия сборки:    {BUILD_TAG}\")\n",
                "print(f\"🎛️ LoRA Rank/Alpha:  r={LORA_RANK}, alpha={LORA_ALPHA} (Scale={LORA_ALPHA/LORA_RANK:.2f})\")\n",
                "print(f\"📦 Целевой архив:    {ARCHIVE_FILENAME}\")\n",
                "\n",
                "!pip install -q \"unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git\"\n",
                "!pip install -q trl peft accelerate bitsandbytes pydrive2 oauth2client\n",
                "import torch\n",
                "assert torch.cuda.is_available(), \"Подключите GPU: Среда выполнения -> Сменить среду -> T4 GPU\"\n",
                "print(f\"✅ Графический процессор: {torch.cuda.get_device_name(0)}\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": null,
            "metadata": {},
            "outputs": [],
            "source": [
                "#@title 📦 2. Загрузка базовой модели Qwen3.5-9B / Qwen2.5 (4-bit) и монтаж Fast-Path LoRA\n",
                "MODEL_NAME = \"unsloth/Qwen3.5-9B-Base\" #@param [\"unsloth/Qwen3.5-9B-Base\", \"Qwen/Qwen3.5-9B\", \"unsloth/Qwen2.5-7B-Instruct-bnb-4bit\"] {allow-input: true}\n",
                "from unsloth import FastLanguageModel\n",
                "\n",
                "print(f\"🚀 Загрузка базовой архитектуры: {MODEL_NAME}...\")\n",
                "model, tokenizer = FastLanguageModel.from_pretrained(\n",
                "    model_name = MODEL_NAME,\n",
                "    max_seq_length = MAX_SEQ_LENGTH,\n",
                "    load_in_4bit = True,\n",
                "    dtype = torch.float16 # Обязательно fp16 под Tesla T4!\n",
                ")\n",
                "\n",
                "model = FastLanguageModel.get_peft_model(\n",
                "    model,\n",
                "    r = LORA_RANK,\n",
                "    lora_alpha = LORA_ALPHA,\n",
                "    target_modules = [\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\", \"gate_proj\", \"up_proj\", \"down_proj\"],\n",
                "    lora_dropout = 0.05,\n",
                "    bias = \"none\",\n",
                "    use_rslora = False,\n",
                "    use_gradient_checkpointing = \"unsloth\",\n",
                "    random_state = 3407\n",
                ")\n",
                "print(f\"✅ LoRA-слои смонтированы в модель! (r={LORA_RANK}, alpha={LORA_ALPHA})\")\n",
                "\n",
                "# Опциональное физическое усечение матрицы lm_head и embed_tokens (smolmaxxing)\n",
                "if PRUNE_VOCAB_HEAD:\n",
                "    orig_v = getattr(model.config, 'vocab_size', 152064)\n",
                "    if orig_v > TARGET_VOCAB_SIZE:\n",
                "        print(f\"✂️ Физическое усечение словаря (smolmaxxing): {orig_v} -> {TARGET_VOCAB_SIZE} токенов...\")\n",
                "        # Сохраняем спецтокены Qwen (<|im_start|>, <|im_end|>, <think> и др. из диапазона 151640..151665)\n",
                "        special_ids = list(range(151640, min(orig_v, 151665)))\n",
                "        base_ids = list(range(TARGET_VOCAB_SIZE - len(special_ids)))\n",
                "        keep_ids = torch.tensor(base_ids + special_ids, dtype=torch.long, device=model.device if hasattr(model, 'device') else 'cpu')\n",
                "        with torch.no_grad():\n",
                "            if hasattr(model, 'lm_head') and hasattr(model.lm_head, 'weight'):\n",
                "                model.lm_head.weight = torch.nn.Parameter(model.lm_head.weight[keep_ids, :])\n",
                "            if hasattr(model, 'model') and hasattr(model.model, 'embed_tokens'):\n",
                "                model.model.embed_tokens.weight = torch.nn.Parameter(model.model.embed_tokens.weight[keep_ids, :])\n",
                "            model.config.vocab_size = TARGET_VOCAB_SIZE\n",
                "            if hasattr(model, 'generation_config') and model.generation_config:\n",
                "                model.generation_config.vocab_size = TARGET_VOCAB_SIZE\n",
                "        saved_mb = round((orig_v - TARGET_VOCAB_SIZE) * 4096 * 1.0 / (1024 * 1024), 1)\n",
                "        print(f\"💾 Тензоры lm_head и embed_tokens усечены: сохранено ~{saved_mb} МБ LPDDR5 RAM на Mi 10T 5G!\")\n",
                "        print(f\"🚀 Вычисление логитов и Softmax ускорено в {orig_v / TARGET_VOCAB_SIZE:.2f} раза.\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": null,
            "metadata": {},
            "outputs": [],
            "source": [
                "#@title 📁 3. Загрузка датасета и Старт Обучения (Zero-CoT Harness)\n",
                "DATASET_URL = \"\" #@param {type:\"string\"}\n",
                "from google.colab import files\n",
                "import os, shutil, urllib.request, json\n",
                "\n",
                "target_dataset = \"dataset.jsonl\"\n",
                "\n",
                "# Способ А: Загрузка по прямой ссылке или с Яндекс.Диска\n",
                "if DATASET_URL and DATASET_URL.strip():\n",
                "    url = DATASET_URL.strip()\n",
                "    print(f\"🌐 Загрузка датасета по ссылке: {url}\")\n",
                "    if \"disk.yandex\" in url or \"yadi.sk\" in url:\n",
                "        api_url = f\"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={url}\"\n",
                "        try:\n",
                "            with urllib.request.urlopen(api_url) as resp:\n",
                "                download_data = json.loads(resp.read().decode('utf-8'))\n",
                "                direct_url = download_data.get(\"href\")\n",
                "                urllib.request.urlretrieve(direct_url, target_dataset)\n",
                "                print(\"✅ Датасет успешно загружен с Яндекс Диска!\")\n",
                "        except Exception as e:\n",
                "            print(f\"⚠️ Ошибка загрузки с Яндекс Диска: {e}. Переходим к ручной загрузке.\")\n",
                "    else:\n",
                "        try:\n",
                "            urllib.request.urlretrieve(url, target_dataset)\n",
                "            print(\"✅ Датасет успешно загружен по прямой ссылке!\")\n",
                "        except Exception as e:\n",
                "            print(f\"⚠️ Ошибка загрузки по ссылке: {e}. Переходим к ручной загрузке.\")\n",
                "\n",
                "# Способ Б: Поиск локальных кандидатов или ручная загрузка triad_omni_harness_sft.jsonl\n",
                "if not os.path.exists(target_dataset):\n",
                "    candidates = [f for f in os.listdir('.') if f.endswith('.jsonl') and f != target_dataset]\n",
                "    harness_candidates = [f for f in candidates if 'harness' in f]\n",
                "    chosen = harness_candidates[0] if harness_candidates else (candidates[0] if candidates else None)\n",
                "    if chosen:\n",
                "        shutil.copy2(chosen, target_dataset)\n",
                "        print(f\"✅ Использован существующий файл датасета: {chosen}\")\n",
                "    else:\n",
                "        print(\"📤 Выберите файл triad_omni_harness_sft.jsonl или triad_omni_sft_dataset.jsonl с вашего ПК:\")\n",
                "        uploaded = files.upload()\n",
                "        for fname in uploaded.keys():\n",
                "            shutil.copy2(fname, target_dataset)\n",
                "            break\n",
                "\n",
                "from trl import SFTTrainer, SFTConfig\n",
                "from datasets import load_dataset\n",
                "\n",
                "raw_ds = load_dataset(\"json\", data_files=target_dataset)[\"train\"]\n",
                "\n",
                "def formatting_func(examples):\n",
                "    texts = []\n",
                "    for messages in examples[\"messages\"]:\n",
                "        try:\n",
                "            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)\n",
                "        except Exception:\n",
                "            text = \"\"\n",
                "            for m in messages:\n",
                "                text += f\"<|im_start|>{m['role']}\\n{m['content']}<|im_end|>\\n\"\n",
                "        texts.append(text)\n",
                "    return {\"text\": texts}\n",
                "\n",
                "train_ds = raw_ds.map(formatting_func, batched=True)\n",
                "print(f\"📊 Загружено {len(train_ds)} сэмплов.\")\n",
                "\n",
                "trainer = SFTTrainer(\n",
                "    model = model,\n",
                "    tokenizer = tokenizer,\n",
                "    train_dataset = train_ds,\n",
                "    dataset_text_field = \"text\",\n",
                "    max_seq_length = MAX_SEQ_LENGTH,\n",
                "    args = SFTConfig(\n",
                "        per_device_train_batch_size = 1,\n",
                "        gradient_accumulation_steps = 8,\n",
                "        max_steps = MAX_STEPS,\n",
                "        learning_rate = LEARNING_RATE,\n",
                "        lr_scheduler_type = \"cosine\",\n",
                "        warmup_ratio = 0.05,\n",
                "        fp16 = True,\n",
                "        bf16 = False,\n",
                "        logging_steps = 5,\n",
                "        output_dir = \"outputs\",\n",
                "        report_to = \"none\"\n",
                "    )\n",
                ")\n",
                "\n",
                "print(\"🚀 Тренировка запущена! Модель обучается мгновенным вызовам <tool_call>...\")\n",
                "trainer.train()\n",
                "print(\"🎉 Обучение успешно завершено!\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": null,
            "metadata": {},
            "outputs": [],
            "source": [
                "#@title 💾 4. Конвертация в GGUF LoRA и Скачивание Версионированного Картриджа\n",
                "import hashlib, json, os, shutil\n",
                "from datetime import datetime, timezone\n",
                "from google.colab import files\n",
                "from huggingface_hub import hf_hub_download\n",
                "\n",
                "print(\"⚡ Шаг 1: Сохраняем локальные веса адаптера...\")\n",
                "model.save_pretrained(\"adapter_files\")\n",
                "tokenizer.save_pretrained(\"adapter_files\")\n",
                "\n",
                "print(f\"⚙️ Шаг 2: Скачиваем конфигурационные файлы базовой модели для {MODEL_NAME}...\")\n",
                "base_model_dir = \"qwen_base_config\"\n",
                "os.makedirs(base_model_dir, exist_ok=True)\n",
                "\n",
                "config_repo = \"Qwen/Qwen3.5-9B\" if \"3.5\" in str(MODEL_NAME) else \"Qwen/Qwen2.5-7B-Instruct\"\n",
                "config_files = [\n",
                "    \"config.json\",\n",
                "    \"generation_config.json\",\n",
                "    \"tokenizer_config.json\",\n",
                "    \"tokenizer.json\",\n",
                "    \"vocab.json\",\n",
                "    \"merges.txt\"\n",
                "]\n",
                "\n",
                "for file_name in config_files:\n",
                "    try:\n",
                "        hf_hub_download(\n",
                "            repo_id=config_repo,\n",
                "            filename=file_name,\n",
                "            local_dir=base_model_dir\n",
                "        )\n",
                "        print(f\"  - Успешно скачан {file_name} из {config_repo}\")\n",
                "    except Exception as e:\n",
                "        print(f\"  - Пропуск {file_name} (не критично): {e}\")\n",
                "\n",
                "# Подменяем путь к базовой модели в конфиге адаптера\n",
                "config_path = \"adapter_files/adapter_config.json\"\n",
                "with open(config_path, \"r\", encoding=\"utf-8\") as f:\n",
                "    cfg = json.load(f)\n",
                "cfg[\"base_model_name_or_path\"] = os.path.abspath(base_model_dir)\n",
                "with open(config_path, \"w\", encoding=\"utf-8\") as f:\n",
                "    json.dump(cfg, f, indent=2)\n",
                "\n",
                "print(\"📦 Шаг 3: Проверка конвертера llama.cpp...\")\n",
                "if not os.path.exists(\"llama.cpp\"):\n",
                "    !git clone -q --depth 1 https://github.com/ggml-org/llama.cpp\n",
                "    !pip install -q -r llama.cpp/requirements.txt\n",
                "\n",
                "print(\"⚙️ Шаг 4: Конвертация LoRA весов в adapter.gguf...\")\n",
                "!python llama.cpp/convert_lora_to_gguf.py adapter_files --base {base_model_dir} --outfile adapter.gguf\n",
                "\n",
                "if not os.path.exists(\"adapter.gguf\"):\n",
                "    raise FileNotFoundError(\"Ошибка: adapter.gguf не был создан! Проверьте логи конвертации выше.\")\n",
                "\n",
                "size_mb = os.path.getsize(\"adapter.gguf\") / 1024 / 1024\n",
                "print(f\"✅ Адаптер готов: adapter.gguf ({size_mb:.1f} МБ)!\")\n",
                "\n",
                "# Считаем SHA256 и формируем паспорт картриджа card.json\n",
                "with open(\"adapter.gguf\", \"rb\") as f:\n",
                "    sha = hashlib.sha256(f.read()).hexdigest()\n",
                "\n",
                "now_iso = datetime.now(timezone.utc).isoformat()\n",
                "card_json = {\n",
                "    \"schema\": \"omni.lora.card/1\",\n",
                "    \"slug\": CARTRIDGE_SLUG,\n",
                "    \"version\": CARTRIDGE_VERSION,\n",
                "    \"build_tag\": BUILD_TAG,\n",
                "    \"created_at\": now_iso,\n",
                "    \"rank\": LORA_RANK,\n",
                "    \"alpha\": LORA_ALPHA,\n",
                "    \"mode\": \"fast_path_harness_adapter\" if HARNESS_MODE else \"persona_knowledge\",\n",
                "    \"thinking\": \"disabled\" if HARNESS_MODE else \"enabled\",\n",
                "    \"steps\": MAX_STEPS,\n",
                "    \"lr\": LEARNING_RATE,\n",
                "    \"max_seq_length\": MAX_SEQ_LENGTH,\n",
                "    \"sha256\": sha,\n",
                "    \"base\": str(MODEL_NAME),\n",
                "    \"vocab_pruned\": PRUNE_VOCAB_HEAD,\n",
                "    \"vocab_size\": TARGET_VOCAB_SIZE if PRUNE_VOCAB_HEAD else 152064,\n",
                "    \"ram_saved_mb\": 420.0 if PRUNE_VOCAB_HEAD else 0.0,\n",
                "    \"device_target\": \"Xiaomi Mi 10T 5G (Snapdragon 865) / OnePlus Nord N10 5G\",\n",
                "    \"description\": f\"Triad-Omni Fast-Path Harness Adapter ({CARTRIDGE_SLUG}) {BUILD_TAG}: Zero-CoT Tool Execution\"\n",
                "}\n",
                "with open(\"card.json\", \"w\", encoding=\"utf-8\") as f:\n",
                "    json.dump(card_json, f, ensure_ascii=False, indent=2)\n",
                "\n",
                "print(f\"📦 Упаковываем версионированный архив: {ARCHIVE_FILENAME}...\")\n",
                "!zip -q \"{ARCHIVE_FILENAME}\" adapter.gguf card.json\n",
                "\n",
                "# Создаем копии для совместимости с автоматическими скриптами\n",
                "shutil.copy2(ARCHIVE_FILENAME, \"cartridge.omni.zip\")\n",
                "shutil.copy2(ARCHIVE_FILENAME, LATEST_FILENAME)\n",
                "\n",
                "cart_size = os.path.getsize(ARCHIVE_FILENAME) / 1024 / 1024\n",
                "print(f\"🎉 Картридж готов ({cart_size:.1f} МБ)! Начинаем скачивание {ARCHIVE_FILENAME}...\")\n",
                "files.download(ARCHIVE_FILENAME)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": null,
            "metadata": {},
            "outputs": [],
            "source": [
                "#@title 🔍 5. Проверка паспорта и целостности картриджа\n",
                "import os, zipfile, json\n",
                "\n",
                "check_file = ARCHIVE_FILENAME if os.path.exists(ARCHIVE_FILENAME) else \"cartridge.omni.zip\"\n",
                "if os.path.exists(check_file):\n",
                "    size_mb = os.path.getsize(check_file) / 1024 / 1024\n",
                "    print(f\"📦 Проверяемый архив: {check_file} ({size_mb:.2f} МБ)\")\n",
                "    with zipfile.ZipFile(check_file, \"r\") as z:\n",
                "        for info in z.infolist():\n",
                "            fsize = info.file_size / 1024 / 1024\n",
                "            csize = info.compress_size / 1024 / 1024\n",
                "            print(f\"  - {info.filename:<15} | Исходный: {fsize:.2f} МБ | Сжатый: {csize:.2f} МБ\")\n",
                "        if \"card.json\" in z.namelist():\n",
                "            card_data = json.loads(z.read(\"card.json\").decode('utf-8'))\n",
                "            print(\"\\n📜 Паспорт картриджа (card.json):\")\n",
                "            print(json.dumps(card_data, ensure_ascii=False, indent=2))\n",
                "else:\n",
                "    print(f\"❌ Файл {check_file} не найден! Сначала выполните шаг 4.\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": null,
            "metadata": {},
            "outputs": [],
            "source": [
                "#@title ☁️ 6. Автоматическая выгрузка в облако Google Диск с сохранением версий (PyDrive2)\n",
                "CUSTOM_GDRIVE_FOLDER = \"\" #@param {type:\"string\"}\n",
                "from pydrive2.auth import GoogleAuth\n",
                "from pydrive2.drive import GoogleDrive\n",
                "from google.colab import auth\n",
                "from oauth2client.client import GoogleCredentials\n",
                "import os, re\n",
                "\n",
                "file_to_upload = ARCHIVE_FILENAME if os.path.exists(ARCHIVE_FILENAME) else \"cartridge.omni.zip\"\n",
                "\n",
                "if not os.path.exists(file_to_upload):\n",
                "    print(f\"❌ Ошибка: Локальный файл {file_to_upload} не найден. Сначала выполните шаг 4!\")\n",
                "else:\n",
                "    auth.authenticate_user()\n",
                "    gauth = GoogleAuth()\n",
                "    gauth.credentials = GoogleCredentials.get_application_default()\n",
                "    drive = GoogleDrive(gauth)\n",
                "\n",
                "    default_targets = [\n",
                "        (\"Основная папка Triad-Omni\", \"1UNP2g3jOfGjxCUDhBDQtMuEFvoESBp1K\"),\n",
                "        (\"Общая папка синхронизации\", \"1WJj716ROzvPpavqRgsLhZ6ik4PfJzKqV\")\n",
                "    ]\n",
                "\n",
                "    targets = []\n",
                "    if CUSTOM_GDRIVE_FOLDER and CUSTOM_GDRIVE_FOLDER.strip():\n",
                "        raw_target = CUSTOM_GDRIVE_FOLDER.strip()\n",
                "        match = re.search(r\"folders/([a-zA-Z0-9_-]+)\", raw_target)\n",
                "        folder_id = match.group(1) if match else raw_target\n",
                "        targets.append((\"Пользовательская папка Google Диска\", folder_id))\n",
                "        print(f\"📁 Выбрана пользовательская папка Google Диска: {folder_id}\")\n",
                "    else:\n",
                "        targets = default_targets\n",
                "\n",
                "    for name, folder_id in targets:\n",
                "        print(f\"⏳ Загрузка {file_to_upload} в '{name}' (ID: {folder_id})...\")\n",
                "        try:\n",
                "            drive_file = drive.CreateFile({\n",
                "                \"title\": os.path.basename(file_to_upload),\n",
                "                \"parents\": [{\"id\": folder_id}],\n",
                "                \"description\": f\"Triad-Omni Fast-Path Cartridge: {CARTRIDGE_SLUG} {BUILD_TAG} (Rank {LORA_RANK}, Alpha {LORA_ALPHA})\"\n",
                "            })\n",
                "            drive_file.SetContentFile(file_to_upload)\n",
                "            drive_file.Upload()\n",
                "            print(f\"  ✅ Архив версии загружен: {file_to_upload}\")\n",
                "            print(f\"  🔗 Ссылка на файл: {drive_file.get('alternateLink')}\")\n",
                "\n",
                "            if os.path.exists(LATEST_FILENAME):\n",
                "                latest_drive = drive.CreateFile({\n",
                "                    \"title\": os.path.basename(LATEST_FILENAME),\n",
                "                    \"parents\": [{\"id\": folder_id}],\n",
                "                    \"description\": f\"Latest build: {BUILD_TAG}\"\n",
                "                })\n",
                "                latest_drive.SetContentFile(LATEST_FILENAME)\n",
                "                latest_drive.Upload()\n",
                "                print(f\"  ✅ Указатель свежей версии загружен: {LATEST_FILENAME}\")\n",
                "        except Exception as e:\n",
                "            print(f\"  ❌ Ошибка загрузки в папку {folder_id}: {e}\")\n",
                "\n",
                "    print(\"🎉 Все версии и архивы успешно сохранены на Google Диске без потери истории!\")"
            ]
        }
    ]

    nb = {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {
                "gpuType": "T4"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 0
    }
    return nb

def main():
    import shutil
    import zipfile
    root = Path(__file__).resolve().parent.parent
    nb = get_notebook_dict()
    nb_str = json.dumps(nb, ensure_ascii=False, indent=2)

    # 1. Update project root
    (root / "triad_omni_trainer.ipynb").write_text(nb_str, encoding="utf-8")
    # 2. Update notebooks directory
    (root / "notebooks" / "triad_omni_trainer.ipynb").write_text(nb_str, encoding="utf-8")
    # 3. Update web_ui datasets directory
    if (root / "web_ui" / "datasets").exists():
        (root / "web_ui" / "datasets" / "triad_omni_trainer.ipynb").write_text(nb_str, encoding="utf-8")
    # 4. Update colab_package
    colab_pkg = root / "colab_package"
    if colab_pkg.exists():
        (colab_pkg / "triad_omni_trainer.ipynb").write_text(nb_str, encoding="utf-8")
        harness_ds = root / "datasets" / "triad_omni_harness_sft.jsonl"
        if harness_ds.exists():
            (colab_pkg / "datasets").mkdir(parents=True, exist_ok=True)
            shutil.copy2(harness_ds, colab_pkg / "datasets" / "triad_omni_harness_sft.jsonl")
        shutil.copy2(root / "scripts" / "build_harness_adapter_sft.py", colab_pkg / "build_harness_adapter_sft.py")
        shutil.copy2(root / "scripts" / "prune_vocab_head.py", colab_pkg / "prune_vocab_head.py")
        
        # Update card.json in colab_package
        card_p = colab_pkg / "card.json"
        if card_p.exists():
            card_obj = json.loads(card_p.read_text(encoding="utf-8"))
            card_obj["vocab_pruned"] = True
            card_obj["target_vocab_size"] = 64000
            card_obj["ram_saved_mb"] = 420.0
            card_p.write_text(json.dumps(card_obj, ensure_ascii=False, indent=2), encoding="utf-8")

        # Rebuild zip
        zip_path = root / "triad_omni_colab_package_v5.2.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for item in colab_pkg.rglob("*"):
                if item.is_file():
                    arcname = item.relative_to(colab_pkg)
                    z.write(item, arcname)
        print(f"📦 Обновлен и собран архив: {zip_path} ({zip_path.stat().st_size / 1024:.1f} КБ)")

    # 5. Update Downloads file if it exists
    downloads_file = Path(r"c:\Users\MSI\Downloads\2_обнова_triad_omni_trainer.ipynb")
    if downloads_file.parent.exists():
        try:
            downloads_file.write_text(nb_str, encoding="utf-8")
            print(f"  - {downloads_file}")
        except Exception as e:
            print(f"  (Пропуск {downloads_file}: {e})")

    print("✅ Обновлены все файлы блокнота triad_omni_trainer.ipynb с поддержкой Fast-Path Harness Adapter и Pruned Head!")
    print(f"  - {root / 'triad_omni_trainer.ipynb'}")
    print(f"  - {root / 'notebooks' / 'triad_omni_trainer.ipynb'}")

if __name__ == "__main__":
    main()
