import urllib.request
import urllib.parse
import http.cookiejar
import re
import sys
from pathlib import Path

file_id = "1ExziQYuM13jFDNxmIPcsGA5Ng3fgiq6V"
target_path = Path(r"d:\для one plus nord n10\cartridges\cartridge_new.zip")

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")]

url = f"https://drive.google.com/uc?id={file_id}&export=download"
print(f"Fetching initial page: {url}")
resp = opener.open(url)
html = resp.read().decode("utf-8", errors="ignore")

form_action = re.search(r'action="([^"]+)"', html)
inputs = dict(re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', html))

if form_action and inputs:
    base_url = form_action.group(1)
    query_str = urllib.parse.urlencode(inputs)
    download_url = f"{base_url}?{query_str}"
else:
    uuid = inputs.get("uuid", "")
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t&uuid={uuid}"

print(f"Opening download URL: {download_url}")
dl_resp = opener.open(download_url)

content_length = dl_resp.headers.get("Content-Length")
content_disp = dl_resp.headers.get("Content-Disposition")
print(f"Headers Content-Length: {content_length} bytes ({int(content_length)/(1024*1024):.2f} MB)" if content_length else "Content-Length: Unknown")
print(f"Headers Content-Disposition: {content_disp}")

print("Downloading full stream...")
total_bytes = 0
with open(target_path, "wb") as f:
    while True:
        chunk = dl_resp.read(1024 * 1024 * 2)
        if not chunk:
            break
        f.write(chunk)
        total_bytes += len(chunk)
        print(f"Downloaded: {total_bytes / (1024 * 1024):.2f} MB", end="\r", flush=True)

print(f"\nFinal bytes written: {total_bytes}")
