with open("scripts/build_updated_web_ui.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("local-cartridge-picker")
if idx != -1:
    print("Found local-cartridge-picker at", idx)
    print(repr(text[idx-100:idx+250]))

idx2 = text.find("function handleLocalCartridgeFile")
if idx2 != -1:
    print("Found function handleLocalCartridgeFile at", idx2)
    print(repr(text[idx2-50:idx2+400]))
