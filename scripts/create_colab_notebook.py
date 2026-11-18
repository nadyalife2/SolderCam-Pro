#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Colab Notebook Generator for LoRA Training
Программно генерирует готовые интерактивные .ipynb ноутбуки под Google Colab
с поддержкой Unsloth, интерактивных параметров #@param, защиты от OOM под Tesla T4,
нативной конвертации в GGUF LoRA (~45 МБ) для смартфонов (Snapdragon 865)
и прямой выгрузкой в Google Диск через PyDrive2 в обход ограничений FUSE.
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from update_trainer_nb import get_notebook_dict

def main():
    out_file = Path("triad_omni_trainer.ipynb")
    if len(sys.argv) > 1:
        out_file = Path(sys.argv[1])
    
    nb = get_notebook_dict()
    out_file.write_text(json.dumps(nb, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Сгенерирован готовый Colab-ноутбук: {out_file.resolve()}")

if __name__ == "__main__":
    main()
