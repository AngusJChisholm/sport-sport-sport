"""Find logos for brands/clubs in deals.json that aren't in entities.json yet.
Asks Brandfetch's brand search for each name and keeps only results whose name matches exactly,
then checks that a symbol or icon exists. Writes logo-proposals.json for review. Slow and polite."""
import json, re, time, unicodedata, urllib.parse, urllib.request, collections
e = json.load(open("entities.json")); cid = e["brandfetch"]; ents = e["entities"]
deals = json.load(open("deals.json"))["deals"]
def n(s):
    s = unicodedata.normalize("NFKD", s); s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\(.*?\)", " ", s.lower()).replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()
known = set()
for v in ents.values():
    known.add(n(v["name"])); known.update(n(a) for a in v.get("aliases", []))
count = collections.Counter()
for d in deals:
    sides = [x.strip() for x in d["deal"].split("×")]
    for side in sides:
        for name in side.split(" / "):
            name = name.strip()
            if name and n(name) not in known: count[name] += 1
UA = {"User-Agent": "Mozilla/5.0 (SSS logo discover)", "Referer": "https://sportsportsport.com.au/"}
def get(url):
    for attempt in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20); time.sleep(1.1); return r.status, r.read()
        except urllib.error.HTTPError as x:
            if x.code != 429: time.sleep(1.1); return x.code, b""
        except Exception: time.sleep(1.1); return 0, b""
        time.sleep(60 * (attempt + 1))
    return 429, b""
props = {}
for name, c in count.most_common(400):
    st, body = get(f"https://api.brandfetch.io/v2/search/{urllib.parse.quote(name)}?c={cid}")
    if st != 200: continue
    try: res = json.loads(body)
    except Exception: continue
    for r in res[:5]:
        if r.get("name") and r.get("domain") and n(r["name"]) == n(name):
            types = [t for t in ("symbol", "icon", "logo") if get(f"https://cdn.brandfetch.io/domain/{urllib.parse.quote(r['domain'])}/w/128/h/128/fallback/404/type/{t}?c={cid}")[0] == 200]
            if types: props[name] = {"domain": r["domain"], "bf": types, "deals": c}
            break
json.dump({"missing": len(count), "proposals": props}, open("logo-report.json", "w"), indent=1, ensure_ascii=False)
print("missing", len(count), "proposed", len(props))
