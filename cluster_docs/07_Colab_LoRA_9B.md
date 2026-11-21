# 07. Еженедельный Пайплайн Дообучения LoRA в Google Colab (Tesla T4)

> Цель: бесплатное, регулярное (1 раз в неделю) дообучение главного текстового мозга **Qwen3.5-9B** на накопленных в процессе работы парах датасета (`sft_<domain>.jsonl`) с использованием бесплатной видеокарты Tesla T4 (16 ГБ VRAM) в Google Colab.

---

## 1. Почему Colab T4, а не локальная видеокарта

| Параметр | Локальная GTX 1050 Ti (ПК) | Google Colab (Tesla T4) |
| :--- | :--- | :--- |
| **Объем видеопамяти (VRAM)** | 4 ГБ | **16 ГБ** |
| **Возможность QLoRA 9B** | ❌ **CUDA OOM** (`device_map={"": 0}` требует ≥7.5 ГБ) | ✅ **Свободно влезает** (занимает ~9.5 ГБ VRAM) |
| **Стоимость** | Бесплатно, но убивает видеокарту перегревом | **Бесплатно** (Free Tier Google Colab) |
| **Время обучения 500 пар** | Невозможно | **~15–20 минут** |

---

## 2. Подготовка датасета на ПК перед отправкой в Colab

На вашем ПК демон курации `auto_lora_trainer.py` автоматически скачивает сырые логи со смартфона Note 4, выполняет дедупликацию по SHA256, очищает служебные теги `<think>` и складывает готовые файлы в папку:
`~/omni_auto_trainer/colab_inbox/sft_<domain>.jsonl`

Формат файла — валидный JSON Lines:
```json
{"messages": [{"role": "user", "content": "...вопрос..."}, {"role": "assistant", "content": "...ответ..."}]}
```

---

## 3. Полный ноутбук для Google Colab (`colab_lora_9b.ipynb`)

Создайте новый ноутбук в [Google Colab](https://colab.research.google.com/), выберите **Среда выполнения -> Сменить тип среды выполнения -> T4 GPU**, загрузите файл датасета `sft_solder.jsonl` (или `sft_reva_android.jsonl`) и выполните следующие ячейки:

### Ячейка 1: Установка Unsloth и зависимостей
```python
!pip install -q unsloth huggingface_hub datasets trl transformers peft
```

### Ячейка 2: Настройка и загрузка базовой модели
```python
import os
import json
import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset
from google.colab import files

# КРИТИЧНО: Базовая модель строго Qwen/Qwen3.5-9B (НЕ Qwen3-8B!)
BASE_MODEL = "Qwen/Qwen3.5-9B"
DOMAIN = "solder"  # solder | reva_android | esp32
DATA_FILE = f"sft_{DOMAIN}.jsonl"

max_seq_length = 2048
dtype = None # Автовыбор (Float16 для T4)
load_in_4bit = True

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
)

# Подключение PEFT LoRA (ранг 8, альфа 16)
model = FastLanguageModel.get_peft_model(
    model,
    r=8,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha=16,
    lora_dropout=0.05,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)
```

### Ячейка 3: Подготовка данных и обучение
```python
# Загрузка и разбиение датасета (90% обучение, 10% валидация)
dataset = load_dataset("json", data_files=DATA_FILE, split="train").train_test_split(test_size=0.1)

def formatting_prompts_func(examples):
    convos = examples["messages"]
    texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
    return {"text": texts}

dataset = dataset.map(formatting_prompts_func, batched=True)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,
    args=SFTConfig(
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        warmup_ratio=0.05,
        num_train_epochs=2,
        learning_rate=1e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=5,
        eval_strategy="epoch",
        output_dir="outputs",
        report_to="none"
    ),
)

trainer_stats = trainer.train()
print("🎉 Обучение завершено успешно!")
```

### Ячейка 4: План А — Конвертация в легкий LoRA GGUF-картридж (~20 МБ)
```python
# Сохраняем LoRA адаптер в формате HuggingFace
model.save_pretrained("lora_adapter")
tokenizer.save_pretrained("lora_adapter")

# Клонируем llama.cpp для конвертации
!git clone --depth 1 https://github.com/ggml-org/llama.cpp
!python llama.cpp/convert_lora_to_gguf.py lora_adapter --base {BASE_MODEL} --outtype q8_0 --outfile lora_9b_{DOMAIN}.gguf

# Скачивание файла адаптера на ПК
files.download(f"lora_9b_{DOMAIN}.gguf")
```

> [!NOTE]
> **План B (Резервный — если llama.cpp на Mi 10T выдает ошибку тензоров LoRA):**  
> Если конкретная сборка `llama.cpp` на архитектуре Qwen3.5 выдает ошибку структуры слоев LoRA, в Colab выполняется прямое слияние весов в полный GGUF:
> ```python
> model.save_pretrained_gguf("merged_model", tokenizer, quantization_method="q4_k_m")
> files.download("merged_model-Q4_K_M.gguf")
> ```
> Примечание: при использовании плана B теряется динамическое переключение слотов, но гарантируется 100% совместимость.

---

## 4. Доставка и деплой на смартфон Mi 10T

После скачивания файла `lora_9b_<domain>.gguf` на ПК, выполните в терминале команду раскатки:

```bash
cd ~/omni_auto_trainer
./deploy_adapter.sh solder ~/Downloads/lora_9b_solder.gguf
```

Скрипт автоматически:
1. Создаст бэкап старого адаптера на Mi 10T (`lora_9b_solder.gguf.bak`).
2. Загрузит новый картридж по SCP.
3. Перезапустит `~/start_brain.sh router`.
4. Проверит статус через `GET http://192.168.1.201:8080/lora-adapters`.
5. Сбросит рабочий слот через `POST :8080/slots/0?action=erase`.
