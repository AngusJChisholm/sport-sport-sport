# DO NOT RUN against Brandfetch again: its terms ban automated logo checks (risk of the client ID being blocked)
# and cap the site at 2,400 logo loads per 5 minutes. Kept for reference; logo_verify.site_icon() is fine on its own.
"""Finds the official website (and so the logo) for every brand and property that has no "domain" yet.
Runs on GitHub (.github/workflows/logo-find.yml), since Brandfetch can't be reached from Claude's sandbox.

For each name it asks Brandfetch's brand search and sorts what comes back into:
  sure   - a result whose name matches exactly (ignoring case, accents, "FC", "Ltd" and the like)
           and that has a logo. If several match, an .au/.nz site wins for ANZ names.
  maybe  - no exact match; the top results are kept for a person to check.
Nothing is written to entities.json here: the report goes to the logo-report branch for review.
Most-dealt names go first. Slow and polite, to stay under Brandfetch's rate limits."""
import json, re, sys, time, threading, unicodedata, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

E = json.load(open("entities.json")); cid = E["brandfetch"]; ents = E["entities"]
deals = json.load(open("deals.json"))["deals"]
UA = {"User-Agent": "Mozilla/5.0 (SSS logo find)", "Referer": "https://sportsportsport.com.au/"}
SUFFIX = r"\b(fc|f c|afc|sc|cf|football club|club|ltd|limited|pty|inc|llc|plc|group|holdings|co|company|corporation|corp|australia|aus|nz|new zealand|official|the)\b"


def base(s):
    s = unicodedata.normalize("NFKD", str(s or "")); s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\(.*?\)", " ", s.lower()).replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def loose(s):
    return re.sub(r"\s+", " ", re.sub(SUFFIX, " ", base(s))).strip()


lock = threading.Lock(); last = [0.0]


def get(url):
    for attempt in range(5):
        with lock:  # one request every 0.55s across both workers
            wait = last[0] + 0.55 - time.time()
            if wait > 0: time.sleep(wait)
            last[0] = time.time()
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20)
            return r.status, r.read()
        except urllib.error.HTTPError as x:
            if x.code != 429: return x.code, b""
        except Exception:
            return 0, b""
        time.sleep(30 * (attempt + 1))
    return 429, b""


def has(domain):
    return [t for t in ("symbol", "icon", "logo")
            if get(f"https://cdn.brandfetch.io/domain/{urllib.parse.quote(domain)}/w/128/h/128/fallback/404/type/{t}?c={cid}")[0] == 200]


# Region of each organisation, from its deals (to prefer .au/.nz sites for ANZ names).
region = {}
for d in deals:
    for side in re.split(r"\s+[×x]\s+", d.get("deal", "")):
        for nm in side.split(" / "):
            region.setdefault(base(nm.strip()), set()).add(d.get("region"))
count = {}
for d in deals:
    for side in re.split(r"\s+[×x]\s+", d.get("deal", "")):
        for nm in side.split(" / "):
            count[base(nm.strip())] = count.get(base(nm.strip()), 0) + 1

todo = [(s, v) for s, v in ents.items() if v.get("k") and not v.get("domain") and not v.get("logo")]
todo.sort(key=lambda x: -max([count.get(base(n), 0) for n in [x[1]["name"]] + x[1].get("aliases", [])] or [0]))
only = sys.argv[1:] and int(sys.argv[1]) or None
if only: todo = todo[:only]
print("to find:", len(todo), flush=True)


def find(item):
    slug, v = item
    names = [v["name"]] + v.get("aliases", [])
    anz = "ANZ" in set().union(*[region.get(base(n), set()) for n in names])
    st, body = get(f"https://api.brandfetch.io/v2/search/{urllib.parse.quote(v['name'])}?c={cid}")
    if st != 200:
        return slug, {"status": st}
    try: res = [r for r in json.loads(body) if r.get("domain") and r.get("name")][:6]
    except Exception: return slug, {"status": "bad json"}
    exact = [r for r in res if base(r["name"]) in {base(n) for n in names}]
    if not exact:
        exact = [r for r in res if loose(r["name"]) and loose(r["name"]) in {loose(n) for n in names}]
    if anz:
        exact.sort(key=lambda r: 0 if re.search(r"\.(au|nz)$", r["domain"]) else 1)
    for r in exact[:2]:
        t = has(r["domain"])
        if t:
            return slug, {"sure": {"domain": r["domain"], "bf": t, "bfName": r["name"]}}
    return slug, {"maybe": [{"name": r["name"], "domain": r["domain"]} for r in res[:3]]}


out = {"sure": {}, "maybe": {}, "none": [], "name": {}}
with ThreadPoolExecutor(2) as ex:
    for i, (slug, r) in enumerate(ex.map(find, todo)):
        out["name"][slug] = ents[slug]["name"]
        if "sure" in r: out["sure"][slug] = r["sure"]
        elif r.get("maybe"): out["maybe"][slug] = r["maybe"]
        else: out["none"].append(slug)
        if i % 50 == 0: print(i, len(out["sure"]), flush=True)
json.dump(out, open("logo-report.json", "w"), indent=1, ensure_ascii=False)
print("sure", len(out["sure"]), "maybe", len(out["maybe"]), "none", len(out["none"]))
