# 🚀 Пакет для дообучения Triad-Omni v5.0 в Google Colab

В этом архиве:
1. 	riad_omni_trainer.ipynb — обновленный 7-шаговый блокнот с выгрузкой GGUF-адаптера (~45 МБ) и автозагрузкой на Google Диск через PyDrive2 в папки 1UNP2g3jOf... и 1WJj716R...
2. 	riad_omni_sft_dataset.jsonl — полный датасет (352 сэмпла) со стилем, кодом, базой знаний кластера Triad-Omni, эталонным реестром стандартов (ГОСТ 21931, ГОСТ Р 56427-2022, IPC-A-610J, IPC-7095E) и базой реверс-инжиниринга REA (Ghidra, JADX, Frida, inspect_model_artifact).
3. 	ochka_plavleniya_sft.jsonl — выделенный датасет (13 сэмплов) по пайплайну Точки Плавления.
4. standards_sft.jsonl — эталонные сэмплы по стандартам и ГОСТам.
5. 
ea_sft.jsonl — сэмплы по REA, анализу APK, дампу прошивок и инспекции GGUF.

### Как запускать:
1. Откройте Google Colab (https://colab.research.google.com).
2. Загрузите файл 	riad_omni_trainer.ipynb.
3. Подключите бесплатный GPU (Среда выполнения -> Сменить среду выполнения -> T4 GPU).
4. Запустите ячейки по порядку (1 -> 2 -> 3 -> 4 -> 5 -> 6).
5. При выполнении шага 3 выберите 	riad_omni_sft_dataset.jsonl.
6. После шага 6 файл cartridge.omni.zip автоматически скачается на ПК и загрузится в обе папки на Google Диске!
