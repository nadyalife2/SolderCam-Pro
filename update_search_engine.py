# -*- coding: utf-8 -*-
import os, sys

target_file = 'd:/для one plus nord n10/omni_gateway.py'
with open(target_file, 'r', encoding='utf-8') as f:
    code = f.read()

robust_search_code = '''
# ----------------- РОБУСТНЫЙ ВЕБ-ПОИСК (DDG API + WIKIPEDIA) -----------------
def web_search_ddg(query, max_results=3):
    """Ищет в интернете через DuckDuckGo Instant Answer API и Wikipedia без блокировок"""
    import ssl, json, re
    ctx = ssl._create_unverified_context()
    results = []

    # 1. DuckDuckGo Instant Answer API
    try:
        url = "https://api.duckduckgo.com/?q=" + urllib.parse.quote(query) + "&format=json&no_html=1"
        req = urllib.request.Request(url, headers={"User-Agent": "TriadOmniCluster/4.0"})
        with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        heading = data.get("Heading", "")
        abstract = data.get("AbstractText", "")
        if abstract:
            results.append(f"• [DuckDuckGo - {heading}]: {abstract}")
        for top in data.get("RelatedTopics", [])[:2]:
            if isinstance(top, dict) and "Text" in top:
                results.append(f"• [DDG Info]: {top['Text']}")
    except Exception:
        pass

    # 2. Wikipedia API (RU & EN)
    if len(results) < 2:
        for lang in ["ru", "en"]:
            try:
                wiki_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&utf8=1"
                wreq = urllib.request.Request(wiki_url, headers={"User-Agent": "TriadOmniCluster/4.0"})
                with urllib.request.urlopen(wreq, timeout=4, context=ctx) as wresp:
                    wdata = json.loads(wresp.read().decode("utf-8", errors="replace"))
                for item in wdata.get("query", {}).get("search", [])[:2]:
                    snip = re.sub(r'<[^>]+>', '', item.get("snippet", "")).strip()
                    if snip:
                        results.append(f"• [Wiki-{lang.upper()} {item.get('title')}]: {snip}")
                if results:
                    break
            except Exception:
                pass

    return "\\n".join(results[:max_results])
'''

# Заменяем старую функцию web_search_ddg
start_mark = '# ----------------- ЛЕГКОВЕСНЫЙ ВЕБ-ПОИСК (DUCKDUCKGO LITE) -----------------'
end_mark = 'def detect_domain(text):'

s_idx = code.find(start_mark)
e_idx = code.find(end_mark)

if s_idx != -1 and e_idx != -1:
    code = code[:s_idx] + robust_search_code.strip() + '\n\n' + code[e_idx:]
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(code)
    print("Replaced with robust DuckDuckGo + Wikipedia Web Search engine!")
else:
    print("Markers not found, s_idx:", s_idx, "e_idx:", e_idx)
