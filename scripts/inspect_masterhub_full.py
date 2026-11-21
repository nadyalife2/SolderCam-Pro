with open('scripts/build_updated_web_ui.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="tab-masterhub"')
idx_end = text.find('<!-- ================= SCRIPT LOGIC', idx)
print(text[idx:idx_end if idx_end != -1 else idx+3000])
