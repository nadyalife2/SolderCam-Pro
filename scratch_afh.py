import urllib.request, re, json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
req = urllib.request.Request('https://androidfilehost.com/?fid=7161016148664787085', headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print("Length:", len(html))
        mirrors = re.findall(r'href="([^"]*download[^"]*)"', html)
        print("Mirrors:", mirrors)
        w_matches = re.findall(r'w=([^"&]+)', html)
        print("w params:", w_matches[:5])
except Exception as e:
    print("Error:", e)
