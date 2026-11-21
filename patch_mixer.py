import re

def patch_mixer_paths():
    with open('mixer_paths.xml', 'r', encoding='utf-8') as f:
        content = f.read()

    # Disable ultrasound-proximity
    content = re.sub(
        r'<path name="ultrasound-proximity">.*?</path>',
        '<path name="ultrasound-proximity">\n        <ctl name="Ultrasound Enable" value="Off" />\n        <ctl name="Ultrasound Mode" value="0" />\n    </path>',
        content,
        flags=re.DOTALL
    )

    # Empty ultrasound-proximity-output paths
    for p in [
        'ultrasound-proximity-output',
        'ultrasound-proximity-output handset',
        'ultrasound-proximity-output headphones',
        'ultrasound-proximity-output headset',
        'ultrasound-proximity-output speaker',
        'ultrasound-proximity-output speaker-and-headphones',
        'ultrasound-proximity-input',
    ]:
        content = re.sub(
            rf'<path name="{p}">.*?</path>',
            f'<path name="{p}">\n    </path>',
            content,
            flags=re.DOTALL
        )

    # Disable ultrasound-gesture1
    content = re.sub(
        r'<path name="ultrasound-gesture1">.*?</path>',
        '<path name="ultrasound-gesture1">\n        <ctl name="Ultrasound Enable" value="Off" />\n        <ctl name="Ultrasound Mode" value="0" />\n    </path>',
        content,
        flags=re.DOTALL
    )

    with open('mixer_paths.xml', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("mixer_paths.xml patched successfully")

def patch_overlay_static():
    with open('mixer_paths_overlay_static.xml', 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(
        r'<path name="ultrasound-proximity">.*?</path>',
        '<path name="ultrasound-proximity">\n        <ctl name="Mi_Ultrasound Enable" value="Off" />\n    </path>',
        content,
        flags=re.DOTALL
    )

    for p in [
        'ultrasound-proximity-output',
        'ultrasound-proximity-output handset',
        'ultrasound-proximity-output speaker',
        'ultrasound-proximity-output speaker-and-headphones',
        'ultrasound-output',
    ]:
        content = re.sub(
            rf'<path name="{p}">.*?</path>',
            f'<path name="{p}">\n    </path>',
            content,
            flags=re.DOTALL
        )

    with open('mixer_paths_overlay_static.xml', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("mixer_paths_overlay_static.xml patched successfully")

if __name__ == '__main__':
    patch_mixer_paths()
    patch_overlay_static()
