import re
import html
import json

with open("gemini_share_real.html", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

# Check for unicode escape sequences like \u043a\u043b\u0430\u0441\u0442\u0435\u0440
unicode_escapes = re.findall(r"(?:\\u[0-9a-fA-F]{4}){5,}", text)
print(f"Found {len(unicode_escapes)} long unicode escape sequences")

decoded_texts = []
for ue in unicode_escapes:
    try:
        dec = bytes(ue, "utf-8").decode("unicode_escape")
        decoded_texts.append(dec)
    except Exception:
        pass

print(f"Decoded {len(decoded_texts)} texts")

with open("decoded_share.txt", "w", encoding="utf-8") as out:
    for idx, dt in enumerate(decoded_texts):
        if len(dt) > 50:
            out.write(f"\n\n=== BLOCK {idx} ===\n{dt}\n")

print("Saved decoded_share.txt")
