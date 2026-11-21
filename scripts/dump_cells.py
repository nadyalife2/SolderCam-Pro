import json

with open(r"c:\Users\MSI\Downloads\2_обнова_triad_omni_trainer.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

for i in [3, 4, 7, 8, 9, 10]:
    print(f"=== CELL {i} ===")
    print("".join(nb["cells"][i]["source"]))
