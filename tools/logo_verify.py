"""Checks a list of official websites for logos and fills the gaps Brandfetch can't.
Input: tools/logo_verify_input.json  {"slug": ["domain1", "domain2"], ...}   (first one that works wins)
For each slug:
  1. Brandfetch: which of symbol / icon / logo exist for the domain (logos.js loads these live).
  2. If Brandfetch has nothing: the organisation's own site icon, taken from the home page
     (SVG icon, apple-touch-icon or the largest PNG icon, at least 96px), saved to assets/logos/<slug>.<ext>.
Writes logo-report.json and the downloaded files; logo-check.yml pushes both to the logo-report branch for review.
Runs on GitHub (Claude's sandbox can't reach these sites)."""
import json, os, re, time, threading, urllib.parse, urllib.request, io
from concurrent.futures import ThreadPoolExecutor

E = json.load(open("entities.json")); cid = E["brandfetch"]
todo = json.load(open("tools/logo_verify_input.json"))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,image/*,*/*;q=0.8"}
lock = threading.Lock(); last = [0.0]
os.makedirs("assets/logos", exist_ok=True)
try:
    from PIL import Image
except Exception:
    Image = None


def get(url, bf=False, limit=4_000_000):
    for attempt in range(4):
        if bf:
            with lock:
                wait = last[0] + 0.55 - time.time()
                if wait > 0: time.sleep(wait)
                last[0] = time.time()
        try:
            h = dict(UA); h["Referer"] = "https://sportsportsport.com.au/"
            r = urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=20)
            return r.status, r.read(limit), r.geturl(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as x:
            if x.code != 429: return x.code, b"", url, ""
        except Exception:
            return 0, b"", url, ""
        time.sleep(30 * (attempt + 1))
    return 429, b"", url, ""


def bf_types(domain):
    return [t for t in ("symbol", "icon", "logo")
            if get(f"https://cdn.brandfetch.io/domain/{urllib.parse.quote(domain)}/w/128/h/128/fallback/404/type/{t}?c={cid}", bf=True)[0] == 200]


def size_of(data, ctype, url):
    if "svg" in ctype or url.lower().split("?")[0].endswith(".svg") or data[:200].lstrip().startswith((b"<svg", b"<?xml")):
        return 9999 if b"<svg" in data[:3000] else 0
    if Image is None: return 0
    try:
        im = Image.open(io.BytesIO(data))
        if getattr(im, "n_frames", 1) > 1 and im.format == "ICO":
            return max(s[0] for s in im.info.get("sizes", [(im.width, im.height)]))
        return min(im.size)
    except Exception:
        return 0


def site_icon(slug, domain):
    st, body, final, _ = get(f"https://{domain}/")
    if st != 200 or not body:
        st, body, final, _ = get(f"https://www.{domain}/")
    cands = []
    if body:
        html = body.decode("utf-8", "ignore")
        for tag in re.findall(r"<link[^>]+>", html, re.I):
            rel = (re.search(r'rel=["\']([^"\']+)', tag, re.I) or [None, ""])[1].lower()
            href = (re.search(r'href=["\']([^"\']+)', tag, re.I) or [None, ""])[1]
            if not href or "icon" not in rel: continue
            sizes = re.search(r'sizes=["\'](\d+)x', tag, re.I)
            score = 9999 if href.lower().split("?")[0].endswith(".svg") else int(sizes.group(1)) if sizes else (180 if "apple" in rel else 32)
            cands.append((score, urllib.parse.urljoin(final, href)))
        m = re.search(r'<link[^>]+rel=["\']manifest["\'][^>]*href=["\']([^"\']+)', html, re.I) or re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']manifest', html, re.I)
        if m:
            mu = urllib.parse.urljoin(final, m.group(1)); s2, mb, _, _ = get(mu)
            try:
                for ic in json.loads(mb).get("icons", []):
                    sz = max([int(x.split("x")[0]) for x in str(ic.get("sizes", "0x0")).split() if "x" in x] or [0])
                    cands.append((sz, urllib.parse.urljoin(mu, ic.get("src", ""))))
            except Exception: pass
    root = f"https://{urllib.parse.urlparse(final).netloc or domain}"
    cands += [(180, root + "/apple-touch-icon.png"), (180, root + "/apple-touch-icon-precomposed.png")]
    for score, url in sorted(cands, key=lambda x: -x[0]):
        s, data, u2, ctype = get(url)
        if s != 200 or not data: continue
        px = size_of(data, ctype, u2)
        if px >= 96:
            ext = "svg" if px == 9999 else (Image.open(io.BytesIO(data)).format or "png").lower().replace("jpeg", "jpg").replace("ico", "png")
            path = f"assets/logos/{slug}.{ext}"
            if ext == "png" and Image is not None:
                im = Image.open(io.BytesIO(data)); im.save(path, "PNG")
            else:
                open(path, "wb").write(data)
            return {"logo": path, "from": u2, "px": px}
    return None


def run(item):
    slug, doms = item
    for d in doms:
        t = bf_types(d)
        if t: return slug, {"domain": d, "bf": t}
    for d in doms:
        s = site_icon(slug, d)
        if s: return slug, dict(s, domain=d)
    return slug, {"none": doms}


rep = {"ok": {}, "none": {}}
with ThreadPoolExecutor(3) as ex:
    for i, (slug, r) in enumerate(ex.map(run, todo.items())):
        (rep["none"] if "none" in r else rep["ok"])[slug] = r
        if i % 50 == 0: print(i, len(rep["ok"]), flush=True)
json.dump(rep, open("logo-report.json", "w"), indent=1, ensure_ascii=False)
print("ok", len(rep["ok"]), "none", len(rep["none"]))
