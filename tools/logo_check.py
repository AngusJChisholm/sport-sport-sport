"""Logo health check. Run by .github/workflows/logo-check.yml (GitHub can reach Brandfetch).
For every entity with a domain: does Brandfetch have a symbol / icon / logo for it?
For every entity without one: what does Brandfetch's brand search suggest?
Writes logo-report.json as a workflow artifact only. No logo images are saved."""
import json, sys, time, urllib.parse, urllib.request, concurrent.futures as cf
e = json.load(open("entities.json")); cid = e["brandfetch"]; ents = e["entities"]
UA = {"User-Agent": "Mozilla/5.0 (SSS logo check)", "Referer": "https://sportsportsport.com.au/"}
def status(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20)
        return r.status, r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as x: return x.code, ""
    except Exception as x: return 0, str(x)[:60]
def check(slug):
    d = ents[slug]["domain"]; out = {}
    for t in ("symbol", "icon", "logo"):
        out[t] = status(f"https://cdn.brandfetch.io/domain/{urllib.parse.quote(d)}/w/128/h/128/fallback/404/type/{t}?c={cid}")[0]
    return slug, out
def search(slug):
    q = urllib.parse.quote(ents[slug]["name"].replace("/", " "))
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"https://api.brandfetch.io/v2/search/{q}?c={cid}", headers=UA), timeout=20)
        res = json.load(r)
        return slug, [{"name": x.get("name"), "domain": x.get("domain"), "q": x.get("qualityScore"), "claimed": x.get("claimed")} for x in res[:5]]
    except Exception as x: return slug, str(x)[:80]
only = sys.argv[1:]  # optional list of slugs to search for
rep = {"checked": {}, "search": {}}
with cf.ThreadPoolExecutor(8) as ex:
    rep["checked"] = dict(ex.map(check, [s for s, v in ents.items() if v.get("domain") and not v.get("logo")]))
    targets = only or [s for s, v in ents.items() if not v.get("domain") and not v.get("logo")]
    rep["search"] = dict(ex.map(search, targets))
# Candidate websites to try for each entity (tools/logo_candidates.json): records what each returns.
import os
if os.path.exists("tools/logo_candidates.json"):
    cand = json.load(open("tools/logo_candidates.json"))
    def trycand(item):
        slug, doms = item; res = {}
        for d in doms:
            res[d] = {t: status(f"https://cdn.brandfetch.io/domain/{urllib.parse.quote(d)}/w/128/h/128/fallback/404/type/{t}?c={cid}")[0] for t in ("symbol", "icon", "logo")}
        return slug, res
    with cf.ThreadPoolExecutor(8) as ex: rep["candidates"] = dict(ex.map(trycand, cand.items()))
json.dump(rep, open("logo-report.json", "w"), indent=1, ensure_ascii=False)
bad = [s for s, v in rep["checked"].items() if all(c != 200 for c in v.values())]
print("checked", len(rep["checked"]), "no logo at all:", len(bad)); print("searched", len(rep["search"]))
