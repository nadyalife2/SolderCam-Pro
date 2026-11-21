import urllib.request, re, json

headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request('https://sourceforge.net/projects/evolution-x/files/billie/', headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        files = re.findall(r'href="([^"]*files/billie/[^"]*)"', html)
        print("Files:", set(files))
except Exception as e:
    print("Error:", e)
