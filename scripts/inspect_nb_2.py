import json

with open(r"c:\Users\MSI\Downloads\2_обнова_triad_omni_trainer.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
for i, cell in enumerate(nb["cells"]):
    cell_type = cell.get("cell_type", "")
    src = "".join(cell.get("source", []))
    title = src.strip().split("\n")[0] if src else "<empty>"
    print(f"Cell {i} [{cell_type}]: {title[:80]}")
