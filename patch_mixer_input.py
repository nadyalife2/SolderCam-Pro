import re

path = r"d:\для one plus nord n10\mixer_paths_overlay_static.xml"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

pattern = r'<path name="ultrasound-input">[\s\S]*?</path>'
replacement = '''<path name="ultrasound-input">
        <!-- Neutralized ultrasound input to avoid 96kHz DMA capture -->
    </path>'''

if re.search(pattern, content):
    new_content = re.sub(pattern, replacement, content)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully patched ultrasound-input in mixer_paths_overlay_static.xml!")
else:
    print("Pattern ultrasound-input not found.")
