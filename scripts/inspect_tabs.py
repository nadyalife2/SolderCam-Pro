import re
with open('scripts/build_updated_web_ui.py', 'r', encoding='utf-8') as f:
    text = f.read()
tabs = re.findall(r'<div id=["\']tab-[^"\']+["\']', text)
print('Tabs found:', tabs)
