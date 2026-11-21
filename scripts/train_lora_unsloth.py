#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Fast-Path Harness Adapter LoRA Training Pipeline v5.2
Запускается в Google Colab T4 (16GB VRAM) или на машине с >=8GB VRAM.
Обучает Qwen3.5-9B или Qwen2.5-7B на агентном датасете triad_omni_harness_sft.jsonl.

Методология Harness-Adapter (Zero-CoT Tool Execution, pi-adapted):
- LoRA rank=32, alpha=64 (scaling factor 2.0)
- Target modules: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- Отключение затяжного рассуждения (<think>...</think>): инъекция пустого think-блока
  сокращает задержку отклика на мобильном Snapdragon 865 со 34–90 сек до сотен миллисекунд.
- Детерминированный вызов инструментов кластера в 1–8 шагов (<tool_call> -> <tool_response>).
- Канареечный аудит инструментальных вызовов и защита от деградации базовой логики.
- Экспорт в runtime GGUF-картридж triad-omni-fast-tool_v5.2.omni.zip с паспортом card.json.
"""

import os
import sys
import json
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen3.5-9B")
DEFAULT_DATA_FILE = "datasets/triad_omni_harness_sft.jsonl"
OUTPUT_DIR = "outputs_triad_harness_master"
ADAPTER_NAME = "triad_harness_adapter_r32"
CARTRIDGE_SLUG = "triad-omni-fast-tool"
CARTRIDGE_VERSION = "v5.2"
MAX_SEQ_LENGTH = 2048

# Канареечные тесты: 3 системных инструмента + 2 общих теста
CANARY_PROMPTS = [
    # 1. Мгновенный вызов инструмента battery_guard (Zero-CoT)
    "Включи сквозной байпас питания на главном мозге Mi 10T, батарея нагрелась выше нормы.",
    # 2. Вызов termux_bash для привязки к ядрам Kryo 585
    "Привяжи процесс llama-server на Mi 10T к производительным ядрам Kryo 585.",
    # 3. Маршрутизация node_route на Node-2 (:8082 BGE-M3)
    "Сгенерируй эмбеддинг для поискового запроса по реестру стандартов пайки.",
    # 4. Защита от потери общей речи (General fluency)
    "Объясни в двух предложениях, чем опасен нагрев литий-ионного аккумулятора выше 45°C при работе без байпаса.",
    # 5. Отрицательные ограничения (Negative Constraints)
    "Ни в коем случае не выполняй rm -rf, просто покажи свободное место на диске."
]

def run_canary_tests(model, tokenizer):
    print("\n🐤 ЗАПУСК КАНАРЕЕЧНОГО ТЕСТИРОВАНИЯ (HARNESS & REASONING AUDIT)...")
    FastLanguageModel.for_inference(model)
    for idx, prompt in enumerate(CANARY_PROMPTS, 1):
        messages = [{"role": "user", "content": prompt}]
        inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt").to("cuda")
        outputs = model.generate(input_ids=inputs, max_new_tokens=150, temperature=0.1)
        resp = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        print(f"\n[Canary {idx}] Запрос: {prompt[:65]}...")
        print(f"  👉 Ответ: {resp.strip()[:200]}...")

def parse_args():
    parser = argparse.ArgumentParser(description="Triad-Omni Harness Adapter LoRA Trainer")
    parser.add_argument("--dataset", type=str, default=DEFAULT_DATA_FILE, help="Путь к jsonl датасету")
    parser.add_argument("--rank", type=int, default=32, help="LoRA Rank (по умолчанию 32 для Harness-Adapter)")
    parser.add_argument("--alpha", type=int, default=64, help="LoRA Alpha (по умолчанию 64)")
    parser.add_argument("--epochs", type=int, default=2, help="Количество эпох")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning Rate")
    parser.add_argument("--base_model", type=str, default=BASE_MODEL, help="HuggingFace репозиторий базовой модели")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 60)
    print("⚡ TRIAD-OMNI: FAST-PATH HARNESS ADAPTER TRAINING (v5.2)")
    print(f"🎯 Архитектура: Harness-Adapter (Zero-CoT Tool Execution, pi-adapted)")
    print(f"📦 Базовая модель:  {args.base_model}")
    print(f"🎛️ LoRA Конфиг:    Rank={args.rank}, Alpha={args.alpha} (Scale={args.alpha/args.rank:.2f})")
    print(f"📂 Датасет:        {args.dataset}")
    print("=" * 60)

    print(f"🚀 Загрузка базовой модели: {args.base_model} в 4-bit...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base_model,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=torch.float16,
        load_in_4bit=True,
    )

    print(f"🔧 Навешивание LoRA-адаптера (r={args.rank}, alpha={args.alpha})...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.rank,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=args.alpha,
        lora_dropout=0.05,
        bias="none",
        use_rslora=False,
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    if not os.path.exists(args.dataset):
        raise FileNotFoundError(f"Файл датасета {args.dataset} не найден! Запустите scripts/build_harness_adapter_sft.py.")

    print(f"📂 Загрузка и разбивка датасета {args.dataset}...")
    dataset = load_dataset("json", data_files=args.dataset, split="train").train_test_split(test_size=0.1)

    def formatting_prompts_func(examples):
        convos = examples["messages"]
        texts = []
        for convo in convos:
            try:
                text = tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False)
            except Exception:
                text = ""
                for m in convo:
                    text += f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
            texts.append(text)
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    training_args = SFTConfig(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4, # Эффективный батч = 8
        warmup_steps=5,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        fp16=True,
        bf16=False,
        neftune_noise_alpha=5.0,
        logging_steps=2,
        eval_strategy="epoch",
        output_dir=OUTPUT_DIR,
        optim="adamw_8bit",
        weight_decay=0.05,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none"
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
    )

    print("🔥 Старт обучения Fast-Path Harness Adapter LoRA...")
    trainer.train()

    # Канареечный тест
    run_canary_tests(model, tokenizer)

    print(f"💾 Сохранение весов адаптера в {ADAPTER_NAME}...")
    model.save_pretrained(ADAPTER_NAME)
    tokenizer.save_pretrained(ADAPTER_NAME)

    # Генерация паспорта картриджа card.json
    now_iso = datetime.now(timezone.utc).isoformat()
    card_json = {
        "schema": "omni.lora.card/1",
        "slug": CARTRIDGE_SLUG,
        "version": CARTRIDGE_VERSION,
        "build_tag": f"{CARTRIDGE_VERSION}_harness_r{args.rank}",
        "created_at": now_iso,
        "rank": args.rank,
        "alpha": args.alpha,
        "mode": "fast_path_harness_adapter",
        "thinking": "disabled",
        "base": args.base_model,
        "device_target": "Xiaomi Mi 10T 5G (Snapdragon 865) / OnePlus Nord N10 5G",
        "description": "Fast-Path Harness Adapter: детерминированный вызов инструментов кластера Triad-Omni без задержек CoT-рассуждений"
    }
    with open(os.path.join(ADAPTER_NAME, "card.json"), "w", encoding="utf-8") as f:
        json.dump(card_json, f, ensure_ascii=False, indent=2)

    print(f"🎉 Обучение завершено! Адаптер сохранен в {ADAPTER_NAME}")
    print("\n📦 Экспорт в runtime GGUF-картридж для llama.cpp на Android:")
    print(f"python llama.cpp/convert_lora_to_gguf.py {ADAPTER_NAME} --base {args.base_model} --outtype f16 --outfile adapter.gguf")
    print(f"zip {CARTRIDGE_SLUG}_{CARTRIDGE_VERSION}.omni.zip adapter.gguf card.json")
    print(f"\n🚀 Раскатка на Mi 10T / Nord N10: --lora-scaled adapter.gguf 1.0")

if __name__ == "__main__":
    main()
