import urllib.request
import urllib.parse
import http.cookiejar
import re

file_id = "1hg0LYA6aB_9qwiGPjbFEyrCNG3VvsBBi"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")]

url = f"https://drive.google.com/uc?id={file_id}&export=download"
resp = opener.open(url)
html = resp.read().decode("utf-8", errors="ignore")

# Find filename and size
name_match = re.search(r'>([^<]+\.(?:zip|apk|tar|gz|gguf|img|bin|json|7z|rar))<', html, re.I)
if not name_match:
    name_match = re.search(r'class="uc-name-size"[^>]*>(.*?)</div>', html, re.DOTALL)

print("Match:", name_match.group(0) if name_match else "No name match")

# Find confirm token
confirm_match = re.search(r'confirm=([0-9A-Za-z_]+)', html)
uuid_match = re.search(r'name="uuid" value="([^"]+)"', html)
print("Confirm token:", confirm_match.group(1) if confirm_match else None)
print("UUID:", uuid_match.group(1) if uuid_match else None)

# Find full download form or link
links = re.findall(r'href="([^"]+download[^"]*)"', html)
print("Download links:", links)
