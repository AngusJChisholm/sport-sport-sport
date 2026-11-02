# DO NOT RUN against Brandfetch again: its terms ban automated logo checks (risk of the client ID being blocked)
# and cap the site at 2,400 logo loads per 5 minutes. Kept for reference; logo_verify.site_icon() is fine on its own.
"""Logo health check. Run by .github/workflows/logo-check.yml (GitHub can reach Brandfetch; Claude's sandbox can't).
mode "candidates": tries each website in tools/logo_candidates.json, stopping at the first that has a logo.
mode "all": checks every mapped entity. Slow and polite, to stay under Brandfetch's rate limit.
Writes logo-report.json only. No logo images are saved."""
import json, sys, time, urllib.parse, urllib.request
e = json.load(open("entities.json")); cid = e["brandfetch"]; ents = e["entities"]
UA = {"User-Agent": "Mozilla/5.0 (SSS logo check)", "Referer": "https://sportsportsport.com.au/"}
def status(url):
    for attempt in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20); code = r.status
        except urllib.error.HTTPError as x: code = x.code
        except Exception: code = 0
        if code != 429: time.sleep(1.1); return code
        time.sleep(60 * (attempt + 1))
    return 429
def types(d, ts=("symbol", "icon")):
    return {t: status(f"https://cdn.brandfetch.io/domain/{urllib.parse.quote(d)}/w/128/h/128/fallback/404/type/{t}?c={cid}") for t in ts}
mode = (sys.argv[1:] or ["candidates"])[0]
rep = {}
if mode == "all":
    rep["checked"] = {s: types(v["domain"], ("symbol", "icon", "logo")) for s, v in ents.items() if v.get("domain") and not v.get("logo")}
else:
    rep["candidates"] = {}
    for slug, doms in json.load(open("tools/logo_candidates.json")).items():
        res = {}
        for d in doms:
            res[d] = types(d)
            if 200 in res[d].values(): break
        rep["candidates"][slug] = res
        print(slug, res, flush=True)
json.dump(rep, open("logo-report.json", "w"), indent=1, ensure_ascii=False)
