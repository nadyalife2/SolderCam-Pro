with open("scripts/omni_fast_router_v4_9.py", "r", encoding="utf-8") as f:
    text = f.read()

target = 'NODE1_URL = os.environ.get("NODE1_URL", "http://127.0.0.1:8080")'
repl = 'NODE1_URL = os.environ.get("NODE1_URL", "http://192.168.31.161:8080")'

if target in text:
    text = text.replace(target, repl, 1)
    with open("scripts/omni_fast_router_v4_9.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("✅ Updated NODE1_URL to 192.168.31.161:8080")
else:
    print("⚠️ Target not found or already updated")
