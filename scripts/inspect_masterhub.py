with open('scripts/build_updated_web_ui.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="tab-masterhub"')
if idx != -1:
    print(text[idx:idx+800])
else:
    print("tab-masterhub not found")
