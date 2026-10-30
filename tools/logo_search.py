# DO NOT RUN against Brandfetch again: its terms ban automated logo checks (risk of the client ID being blocked)
# and cap the site at 2,400 logo loads per 5 minutes. Kept for reference; logo_verify.site_icon() is fine on its own.
"""Finds official websites for names Brandfetch couldn't place. Runs on GitHub (logo-check.yml mode "search").
Input: tools/logo_search_input.json  {"slug": {"name": "...", "context": "Brand × Club (Sport)", "page": "club partner page url or ''"}}
1. If the deal came from a club's partner page, read that page and take the link next to the partner's logo or name.
2. Otherwise search the web (DuckDuckGo's HTML page) for "<name> <context>" and try the top company sites.
A site is only kept if its home page title or logo alt text contains the name. Then Brandfetch is checked, and if it
has no logo the site's own icon is saved (same as logo_verify.py). Report: logo-report.json (+ logos/), for review."""
import json, re, urllib.parse, unicodedata, sys
sys.path.insert(0, "tools")
import logo_verify as V   # reuses get(), bf_types(), site_icon()

todo = json.load(open("tools/logo_search_input.json"))
SKIP = re.compile(r"(facebook|instagram|linkedin|twitter|x\.com|youtube|tiktok|wikipedia|google|bing|duckduckgo|apple\.com|amazon\.|ebay|yelp|crunchbase|zoominfo|bloomberg|reuters|news|sport|afl\.com|nrl\.com|espn|abc\.net|smh\.com|theage|heraldsun|9now|7news|fox|seek\.com|indeed|glassdoor|yellowpages|truelocal|hotfrog|dnb\.com|opencorporates|abr\.business|pinterest|reddit|medium|wordpress\.com|blogspot|wix\.com|squarespace\.com|github)", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")); s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def core(name):
    w = [x for x in norm(name).split() if x not in {"the", "and", "co", "group", "pty", "ltd", "australia", "services", "company"}]
    return " ".join(w) or norm(name)


def domain_of(u):
    d = urllib.parse.urlparse(u).netloc.lower()
    return d[4:] if d.startswith("www.") else d


def title_ok(domain, name):
    st, body, final, _ = V.get(f"https://{domain}/")
    if st != 200 or not body: return False
    h = body[:300000].decode("utf-8", "ignore")
    t = " ".join(re.findall(r"<title[^>]*>(.*?)</title>", h, re.I | re.S)[:1] + re.findall(r'og:site_name["\'][^>]*content=["\']([^"\']+)', h, re.I)[:1]
                 + re.findall(r'<img[^>]+alt=["\']([^"\']{2,80})', h, re.I)[:6])
    c = core(name)
    return bool(c) and (c in norm(t) or c.replace(" ", "") in norm(t).replace(" ", "") or c.replace(" ", "") in domain.replace("-", ""))


def from_partner_page(page, name):
    st, body, final, _ = V.get(page)
    if st != 200: return []
    h = body.decode("utf-8", "ignore"); c = core(name); out = []
    for m in re.finditer(r"<a\b[^>]*href=[\"'](https?://[^\"']+)[\"'][^>]*>(.*?)</a>", h, re.I | re.S):
        href, inner = m.group(1), m.group(2)
        d = domain_of(href)
        if not d or d in domain_of(final) or SKIP.search(d): continue
        label = " ".join(re.findall(r'(?:alt|title|aria-label)=["\']([^"\']+)', m.group(0), re.I)) + " " + re.sub(r"<[^>]+>", " ", inner)
        if c and (c in norm(label) or c.replace(" ", "") in d.replace("-", "").replace(".", "")):
            out.append(d)
    return list(dict.fromkeys(out))


def from_search(name, context):
    q = urllib.parse.quote(f"{name} {context} official site")
    st, body, _, _ = V.get(f"https://html.duckduckgo.com/html/?q={q}")
    if st != 200: return []
    links = re.findall(r'class="result__a"[^>]*href="([^"]+)"', body.decode("utf-8", "ignore"))
    out = []
    for l in links:
        m = re.search(r"uddg=([^&]+)", l)
        u = urllib.parse.unquote(m.group(1)) if m else l
        d = domain_of(u)
        if d and not SKIP.search(d): out.append(d)
    return list(dict.fromkeys(out))[:5]


def run(item):
    slug, x = item
    cands = (from_partner_page(x["page"], x["name"]) if x.get("page") else [])
    via = "partner page" if cands else "search"
    if not cands: cands = from_search(x["name"], x.get("context", ""))
    for d in cands:
        if via == "partner page" or title_ok(d, x["name"]):
            t = V.bf_types(d)
            if t: return slug, {"domain": d, "bf": t, "via": via}
            s = V.site_icon(slug, d)
            if s: return slug, dict(s, domain=d, via=via)
            return slug, {"domain": d, "via": via, "nologo": True}
    return slug, {"none": cands}


rep = {"ok": {}, "none": {}}
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(3) as ex:
    for slug, r in ex.map(run, todo.items()):
        (rep["none"] if "none" in r else rep["ok"])[slug] = r
json.dump(rep, open("logo-report.json", "w"), indent=1, ensure_ascii=False)
print("ok", len(rep["ok"]), "none", len(rep["none"]))
