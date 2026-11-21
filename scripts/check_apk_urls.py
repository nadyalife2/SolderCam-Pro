import zipfile
import re

with zipfile.ZipFile(r"d:\для one plus nord n10\melvin_src\ai.melvin.app.apk") as z:
    for name in z.namelist():
        data = z.read(name)
        # Search for localhost / 127.0.0.1 / http
        matches = re.findall(rb"https?://[a-zA-Z0-9\.\:\-]+", data)
        if matches:
            print(f"File {name}: {set(matches)}")
        port_matches = re.findall(rb"80[0-9]{2}", data)
        if port_matches:
            print(f"Ports in {name}: {set(port_matches)}")
