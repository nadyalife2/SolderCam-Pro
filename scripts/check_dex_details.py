import zipfile
import re

with zipfile.ZipFile(r"d:\для one plus nord n10\melvin_src\ai.melvin.app.apk") as z:
    dex = z.read("classes.dex")
    idx = dex.find(b"127.0.0.1")
    while idx != -1:
        start = max(0, idx - 50)
        end = min(len(dex), idx + 100)
        chunk = dex[start:end]
        # Filter printable
        printable = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
        print("MATCH:", printable)
        idx = dex.find(b"127.0.0.1", idx + 1)
