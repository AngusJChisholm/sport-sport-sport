"""Builds a real page for every brand and property: brands/<slug>.html and properties/<slug>.html.

Each page is profile.html with the name, numbers and deal list already written into the HTML, so search
engines can read it and it shows before any script runs. The same profile script then takes over for
filters, logos and the category map. Also writes sitemap.xml and marks each entity in entities.json
with "k": "b" (brand) or "p" (property) so links across the site point at these pages.

Run after deals.json changes: python3 tools/build_profiles.py   (only changed pages are rewritten)
"""
import json, re, unicodedata, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://sportsportsport.com.au"


def strip_marks(x):
    return "".join(c for c in unicodedata.normalize("NFKD", x) if not unicodedata.combining(c))


def norm(x):  # same as assets/logos.js norm()
    x = strip_marks(str(x or "")).lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9()]+", " ", x).strip()


def slugify(x):  # same as assets/logos.js slugify()
    x = re.sub(r"\(.*?\)", " ", strip_marks(str(x or ""))).lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", x).strip("-")


def split(deal):
    p = re.split(r"\s+[×x]\s+", str(deal or ""))
    return (p[0].strip(), " × ".join(p[1:]).strip()) if len(p) >= 2 else (str(deal or "").strip(), "")


def many(side):
    return [s.strip() for s in re.split(r"\s+/\s+", side) if s.strip()]


def sort_key(d):
    return d.get("date") or ((d.get("month") or "0000-00") + "-00")


def fmt(d):
    import datetime
    if d.get("date"):
        dt = datetime.date.fromisoformat(d["date"])
        return dt.strftime("%d %b %Y")
    if d.get("month"):
        dt = datetime.date.fromisoformat(d["month"] + "-01")
        return dt.strftime("%b %Y")
    return "Current partner"


def esc(x):
    return html.escape(str(x or ""), quote=True)


def main():
    E = json.loads((ROOT / "entities.json").read_text(encoding="utf-8"))
    ent = E["entities"]
    look = {}
    for slug, x in ent.items():
        look[norm(x["name"])] = slug
        for a in x.get("aliases", []):
            look[norm(a)] = slug
    resolve = lambda n: look.get(norm(n)) or slugify(n)
    deals = json.loads((ROOT / "deals.json").read_text(encoding="utf-8"))["deals"]
    deals.sort(key=sort_key, reverse=True)

    recs = {}
    for d in deals:
        b, p = split(d.get("deal"))
        bs, ps = [resolve(n) for n in many(b)], ([resolve(n) for n in many(p)] if p else [])
        names = dict(zip(bs, many(b)))
        names.update(zip(ps, many(p) if p else []))
        for side, lst, other in (("b", bs, ps), ("p", ps, bs)):
            for s in lst:
                r = recs.setdefault(s, {"nB": 0, "nP": 0, "deals": [], "partners": {}, "sports": {}, "name": ent.get(s, {}).get("name") or names.get(s, s)})
                r["nB" if side == "b" else "nP"] += 1
                r["deals"].append((d, side))
                if d.get("sport"):
                    r["sports"][d["sport"]] = r["sports"].get(d["sport"], 0) + 1
                for o in other:
                    r["partners"][o] = r["partners"].get(o, 0) + 1

    tpl = (ROOT / "profile.html").read_text(encoding="utf-8")
    pname = lambda s: ent.get(s, {}).get("name") or recs.get(s, {}).get("name") or s
    written, kept, urls = 0, set(), []
    ent_changed = False
    for slug, r in sorted(recs.items()):
        if not slug:
            continue
        kind = "b" if r["nB"] >= r["nP"] else "p"
        folder = "brands" if kind == "b" else "properties"
        if slug in ent and ent[slug].get("k") != kind:
            ent[slug]["k"] = kind
            ent_changed = True
        e = ent.get(slug, {})
        name = r["name"]
        n = len(r["deals"])
        sports = sorted(r["sports"], key=lambda k: -r["sports"][k])
        partners = sorted(r["partners"], key=lambda k: (-r["partners"][k], pname(k)))
        group = e.get("cat") if kind == "b" else e.get("ptype")
        label = ("Brand" + (f" · {group}" if group else "")) if kind == "b" else (group or "Property")
        top_p = ", ".join(pname(k) for k in partners[:6])
        dated = [d for d, _ in r["deals"] if d.get("date") or d.get("month")] or [d for d, _ in r["deals"]]
        latest, first = dated[0], dated[-1]
        if kind == "b":
            desc = f"{name} sponsorship deals: {n} filed across {', '.join(sports[:3])}. Partners include {top_p}." if top_p else f"{name} sponsorship deals in sport."
            title = f"{name} sponsorships and sport partners"
        else:
            desc = f"{name} sponsors and partners: {n} deals filed. Partners include {top_p}." if top_p else f"{name} sponsors and partners."
            title = f"{name} sponsors and partners"
        url = f"{SITE}/{folder}/{slug}.html"
        stats = "".join(f'<div class="stat"><b>{esc(v)}</b><span>{esc(l)}</span></div>' for v, l in [
            (n, "deal filed" if n == 1 else "deals filed"), (len(sports), "sport" if len(sports) == 1 else "sports"),
            (fmt(latest), "latest deal"), (fmt(first), "first filed")])
        rows = []
        for d, side in r["deals"]:
            nm = esc(d.get("deal"))
            if d.get("slug") and d.get("article"):
                nm = f'<a href="articles/{esc(d["slug"])}.html"><b>{nm}</b></a>'
            elif str(d.get("url") or "").startswith("https://"):
                nm = f'<a href="{esc(d["url"])}" target="_blank" rel="noopener"><b>{nm}</b></a>'
            else:
                nm = f"<b>{nm}</b>"
            ends = (("c. " if d.get("endsEst") else "") + str(d["ends"])) if d.get("ends") else "–"
            rows.append(f'<div class="ar-r"><span class="d">{esc(fmt(d))}</span><span class="dl">{nm}</span><span class="s">{esc(d.get("sport"))}</span><span class="t">{esc(d.get("tier") or d.get("type"))}</span><span class="d">{esc(ends)}</span></div>')
        ptiles = "".join(f'<a class="pt" href="{esc(("brands" if recs.get(k, {}).get("nB", 0) >= recs.get(k, {}).get("nP", 0) else "properties"))}/{esc(k)}.html"><b>{esc(pname(k))}</b><span class="k">{r["partners"][k]} deal{"s" if r["partners"][k] > 1 else ""}</span></a>' for k in partners)
        jsonld = json.dumps({"@context": "https://schema.org", "@type": "Organization" if kind == "b" or group not in ("Athlete & talent",) else "Person",
                             "name": name, "url": url, **({"sameAs": [f"https://{e['domain']}"]} if e.get("domain") else {})}, ensure_ascii=False)

        page = tpl
        page = page.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<base href="../">', 1)
        page = re.sub(r"<title>.*?</title>", lambda m: f"<title>{esc(title)} | Sport Sport Sport</title>", page, count=1)
        page = re.sub(r'<meta name="description" content=".*?">', lambda m: f'<meta name="description" content="{esc(desc)}">\n<link rel="canonical" href="{url}">\n<meta property="og:title" content="{esc(title)}">\n<meta property="og:description" content="{esc(desc)}">\n<meta property="og:url" content="{url}">\n<script type="application/ld+json">{jsonld}</script>', page, count=1)
        page = page.replace("<body>", f'<body data-id="{esc(slug)}">', 1)
        page = page.replace('<span id="crName" style="color:var(--ink)">Loading</span>', f'<span id="crName" style="color:var(--ink)">{esc(name)}</span>')
        page = page.replace('<span class="lbl mute-l" id="kind"></span>', f'<span class="lbl mute-l" id="kind">{esc(label)}</span>')
        page = page.replace('<h1 class="disp" id="name">Loading</h1>', f'<h1 class="disp" id="name">{esc(name)}</h1>')
        page = page.replace('<div class="stats" id="stats"></div>', f'<div class="stats" id="stats">{stats}</div>')
        page = page.replace('<div class="pg" id="pGrid"></div>', f'<div class="pg" id="pGrid">{ptiles}</div>')
        page = page.replace('<section class="sec" id="partners" hidden>', '<section class="sec" id="partners">' if partners else '<section class="sec" id="partners" hidden>')
        page = page.replace('<span class="lbl mute-l" id="dCount"></span>', f'<span class="lbl mute-l" id="dCount">{n} deal{"s" if n != 1 else ""}</span>')
        page = page.replace('<div id="list"></div>', f'<div id="list">{"".join(rows)}</div>')
        page = page.replace('<section class="sec" id="deals" hidden style="padding-top:0">', '<section class="sec" id="deals" style="padding-top:0">')

        out = ROOT / folder / f"{slug}.html"
        out.parent.mkdir(exist_ok=True)
        kept.add(out)
        if not out.exists() or out.read_text(encoding="utf-8") != page:
            out.write_text(page, encoding="utf-8")
            written += 1
        urls.append((url, sort_key(latest)))

    # Remove pages for names that no longer exist (merged or renamed).
    removed = 0
    for folder in ("brands", "properties"):
        for f in (ROOT / folder).glob("*.html"):
            if f not in kept:
                f.unlink()
                removed += 1

    if ent_changed:
        (ROOT / "entities.json").write_text(json.dumps(E, ensure_ascii=False, indent=1), encoding="utf-8")

    static = ["", "news.html", "brands.html", "properties.html", "insights.html", "categories.html", "renewals.html", "leagues.html", "compare.html"]
    arts = sorted(p.name for p in (ROOT / "articles").glob("*.html"))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{SITE}/{p}</loc></url>" for p in static]
    sm += [f"<url><loc>{SITE}/articles/{a}</loc></url>" for a in arts]
    sm += [f"<url><loc>{u}</loc><lastmod>{lm[:10] if lm[8:10] != '00' else lm[:7] + '-01'}</lastmod></url>" for u, lm in urls]
    sm.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    print(f"{len(urls)} profile pages ({written} written, {removed} removed), sitemap.xml updated")


if __name__ == "__main__":
    main()
