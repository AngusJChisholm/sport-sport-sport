"""Render the two daily LinkedIn graphics (1080x1080) in the fixed house layout.

    python3 tools/linkedin_graphics.py spec.json out_dir

spec.json: {"date":"YYYY-MM-DD","headline_lines":["MONACO'S","SHIRT FOR","EUROPE","ONLY."],
 "highlight":"EUROPE","deal":"Brand x Property","descriptor":"Deal type",
 "others":[{"deal":"Brand x Property","sub":"Sport - deal type"}, ...]}
Optional "image": the lead's photo ("assets/..." file or an images.unsplash.com link,
same as its deals.json "image"). Slide 1 shows it fading into white; without it the top is plain light grey.
Writes sss-<date>-slide1.png (headline) and sss-<date>-slide2.png (other deals).
"""
import base64, html, json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
e = lambda s: html.escape(str(s))

def css():
    f = base64.b64encode((ROOT / "assets/fonts/Archivo[wdth,wght].ttf").read_bytes()).decode()
    return f"""@font-face{{font-family:Archivo;src:url(data:font/ttf;base64,{f});font-weight:100 900;font-stretch:62% 125%}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;background:#000;color:#fff;font-family:Archivo;position:relative;overflow:hidden;-webkit-font-smoothing:antialiased}}
.lab{{position:absolute;left:97px;top:96px;font-weight:800;font-size:25px;letter-spacing:.2em;text-transform:uppercase}}
.wm{{position:absolute;right:97px;bottom:84px;width:124px}}
.v{{color:#D2FF3C}}"""

def wordmark(colour="white"):
    return base64.b64encode((ROOT / f"assets/wordmark-{colour}.svg").read_bytes()).decode()

def photo(img):
    img = str(img or "")
    if re.fullmatch(r"assets/[\w/.-]+\.(jpe?g|png|webp)", img) and (ROOT / img).exists():
        return "data:image/jpeg;base64," + base64.b64encode((ROOT / img).read_bytes()).decode()
    m = re.match(r"^https://images\.unsplash\.com/(photo-[\w-]+)", img)
    if m and (ROOT / "assets/img/u" / f"{m.group(1)}.jpg").exists():  # site copy works offline too
        return "data:image/jpeg;base64," + base64.b64encode((ROOT / "assets/img/u" / f"{m.group(1)}.jpg").read_bytes()).decode()
    return f"https://images.unsplash.com/{m.group(1)}?w=1080&h=1080&q=80&auto=format&fit=crop" if m else ""

# LinkedIn look (2 Nov 2026): white and editorial, more buttoned-up than Instagram. Left-aligned,
# hard-edged photo panel, no volt fills: volt appears only as a thin accent bar. Same photo as everywhere.
from datetime import date as _date

def nice_date(d):
    try:
        x = _date.fromisoformat(d)
        return f"{x.day} {x.strftime('%B %Y')}"
    except Exception:
        return d

PRO_CSS = """
body{background:#fff;color:#111}
.kick{display:flex;align-items:center;gap:16px;font-weight:800;font-size:21px;letter-spacing:.16em;text-transform:uppercase;color:#111}
.kick i{display:block;width:44px;height:6px;background:#D2FF3C}
.kick em{font-style:normal;font-weight:600;color:#7A7A74}
.ft{position:absolute;left:80px;right:80px;bottom:64px;display:flex;justify-content:space-between;align-items:flex-end;border-top:1px solid #DEDED8;padding-top:24px}
.ft img{width:96px}.ft div{font-weight:600;font-size:19px;letter-spacing:.12em;text-transform:uppercase;color:#7A7A74}
"""

def slide1(s):
    src = photo(s.get("image"))
    head = " ".join(l.strip() for l in s["headline_lines"])
    pair = e(s["deal"]).replace(" x ", " &times; ", 1)
    ph = (f'<div class="ph" style="background-image:url(\'{src}\')"></div>') if src else '<div class="ph" style="background:#EDEDE8"></div>'
    return f"""<style>{css()}{PRO_CSS}
.ph{{position:absolute;left:0;right:0;top:0;height:520px;background-position:center 30%;background-size:cover}}
.txt{{position:absolute;left:80px;right:80px;top:576px}}
.h{{margin-top:22px;font-weight:800;font-size:96px;font-stretch:75%;line-height:.92;text-transform:uppercase;letter-spacing:-.005em;color:#111}}
.d{{margin-top:22px;font-weight:500;font-size:26px;color:#5C5C57}}.d b{{font-weight:800;color:#111}}</style>
{ph}<div class="txt"><div class="kick"><i></i>Deal of the day <em>&middot; {e(nice_date(s.get("date","")))}</em></div>
<div class="h" data-fit>{e(head)}</div>
<div class="d"><b>{pair}</b> &nbsp;|&nbsp; {e(s["descriptor"])}</div></div>
<div class="ft"><img src="data:image/svg+xml;base64,{wordmark('black')}"><div>sportsportsport.com.au</div></div>"""

def slide2(s):
    """Round-up as a clean table: deal on the left, sport and deal type on the right."""
    rows = []
    for o in s["others"][:5]:
        sport, _, rest = str(o.get("sub") or "").partition(" - ")
        if not rest:
            sport, rest = "", sport
        rows.append(f'<div class="r"><b>{e(o["deal"])}</b><div class="m"><span class="sp">{e(sport)}</span>'
                    f'<span>{e(rest[:1].upper() + rest[1:])}</span></div></div>')
    n = len(rows)
    big = 52 if n <= 3 else 44 if n == 4 else 36
    return f"""<style>{css()}{PRO_CSS}
.top{{position:absolute;left:80px;right:80px;top:80px}}
.t{{margin-top:22px;font-weight:800;font-size:74px;font-stretch:75%;line-height:.95;text-transform:uppercase;color:#111}}
.rows{{position:absolute;left:80px;right:80px;top:300px;border-top:3px solid #111}}
.r{{display:flex;justify-content:space-between;align-items:center;gap:30px;padding:{int(big*.62)}px 0;border-bottom:1px solid #DEDED8}}
.r b{{font-weight:800;font-size:{big}px;font-stretch:78%;line-height:1;text-transform:uppercase;color:#111}}
.r .m{{text-align:right;flex-shrink:0;max-width:40%}}
.r .m span{{display:block;font-size:22px;color:#5C5C57;line-height:1.3}}
.r .m .sp{{font-weight:800;font-size:18px;letter-spacing:.16em;text-transform:uppercase;color:#111;margin-bottom:4px}}</style>
<div class="top"><div class="kick"><i></i>Today's other deals <em>&middot; {e(nice_date(s.get("date","")))}</em></div>
<div class="t">Also signed today.</div></div>
<div class="rows">{"".join(rows)}</div>
<div class="ft"><img src="data:image/svg+xml;base64,{wordmark('black')}"><div>Every deal, filed: sportsportsport.com.au</div></div>"""

def render(spec, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1080})
        for n, h in (("slide1", slide1(spec)), ("slide2", slide2(spec))):
            pg.set_content(h, wait_until="networkidle"); pg.evaluate("document.fonts.ready")
            assert pg.evaluate('document.fonts.check("800 50px Archivo")')
            pg.screenshot(path=str(out / f"sss-{spec['date']}-{n}.png"))
        b.close()

if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
