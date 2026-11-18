import urllib.request
import urllib.parse
import http.cookiejar
import re
from pathlib import Path

file_id = "1hg0LYA6aB_9qwiGPjbFEyrCNG3VvsBBi"
target_path = Path(r"d:\для one plus nord n10\cartridges\cartridge.omni.zip")

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")]

url = f"https://drive.google.com/uc?id={file_id}&export=download"
print(f"Fetching initial page: {url}")
resp = opener.open(url)
html = resp.read().decode("utf-8", errors="ignore")

form_action = re.search(r'action="([^"]+)"', html)
inputs = dict(re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', html))

print(f"Form action: {form_action.group(1) if form_action else 'None'}")
print(f"Form inputs: {inputs}")

if form_action and inputs:
    base_url = form_action.group(1)
    query_str = urllib.parse.urlencode(inputs)
    download_url = f"{base_url}?{query_str}"
    print(f"Sending GET request to {download_url}...")
    dl_resp = opener.open(download_url)
else:
    uuid = inputs.get("uuid", "")
    dl_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t&uuid={uuid}"
    print(f"Trying fallback URL: {dl_url}")
    dl_resp = opener.open(dl_url)

print("Starting download...")
total_bytes = 0
with open(target_path, "wb") as f:
    while True:
        chunk = dl_resp.read(1024 * 1024 * 4) # 4MB chunks
        if not chunk:
            break
        f.write(chunk)
        total_bytes += len(chunk)
        print(f"Downloaded: {total_bytes / (1024 * 1024):.2f} MB", end="\r")

print(f"\n✅ Download complete! File saved to {target_path} ({total_bytes / (1024*1024):.2f} MB)")
