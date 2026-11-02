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

# House look (2 Nov 2026): white, centred, matching the Instagram cover. Volt is only ever a fill
# behind black type. Slide 1 = the lead's photo fading into white; slide 2 = white round-up.
LABEL = ("font-weight:800;font-size:24px;letter-spacing:.14em;text-transform:uppercase")

def brand(tag):
    return (f'<div class="br">Sport Sport Sport <span>/ {e(tag)}</span></div>')

def slide1(s):
    src = photo(s.get("image"))
    head = " ".join(l.strip() for l in s["headline_lines"])
    hl = s.get("highlight", "").strip(".,!?' ")
    words = []
    for w in head.split():
        core = w.strip(".,!?'")
        words.append(f'<span class="v">{e(w)}</span>' if hl and core.upper() == hl.upper() else e(w))
    pair = e(s["deal"]).replace(" x ", " &times; ", 1)
    ph = (f'<div class="ph" style="background-image:url(\'{src}\')"></div>') if src else '<div class="ph" style="background:#EDEDE8"></div>'
    return f"""<style>{css()}
body{{background:#fff;color:#000}}
.ph{{position:absolute;inset:0 0 auto 0;height:760px;background-position:center 30%;background-size:cover}}
.fade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.25) 0%,rgba(0,0,0,0) 14%,rgba(255,255,255,0) 40%,rgba(255,255,255,.85) 55%,#fff 66%,#fff 100%)}}
.low{{position:absolute;left:70px;right:70px;bottom:70px;display:flex;flex-direction:column;align-items:center;text-align:center}}
.br{{{LABEL}}}.br span{{background:#D2FF3C;padding:.12em .3em 0}}
.h{{margin-top:18px;font-weight:800;font-size:118px;font-stretch:68%;line-height:.9;text-transform:uppercase;letter-spacing:-.005em}}
.h .v{{color:#000;background:#D2FF3C;padding:0 .06em}}
.d{{margin-top:22px;font-weight:600;font-size:23px;letter-spacing:.14em;text-transform:uppercase;color:#5C5C57}}.d b{{color:#000;font-weight:800}}</style>
{ph}<div class="fade"></div>
<div class="low">{brand("Deal of the day")}<div class="h">{" ".join(words)}</div>
<div class="d"><b>{pair}</b> &middot; {e(s["descriptor"])}</div></div>"""

def slide2(s):
    """White round-up in the same centred style. Volt is a fill behind black type, never text on white."""
    rows = []
    for o in s["others"][:5]:
        sport, _, rest = str(o.get("sub") or "").partition(" - ")
        if not rest:
            sport, rest = "", sport
        rows.append('<div class="r">' + (f'<i>{e(sport)}</i>' if sport else "")
                    + f'<b>{e(o["deal"])}</b>' + (f'<span>{e(rest)}</span>' if rest else "") + "</div>")
    n = len(rows)
    big = 62 if n <= 3 else 52 if n == 4 else 44
    return f"""<style>{css()}
body{{background:#fff;color:#000}}
.top{{position:absolute;left:0;right:0;top:64px;display:flex;justify-content:center}}
.br{{{LABEL}}}.br span{{background:#D2FF3C;padding:.12em .3em 0}}
.rows{{position:absolute;left:90px;right:90px;top:150px;bottom:190px;display:flex;flex-direction:column;justify-content:center;text-align:center}}
.r{{padding:{int(big*.42)}px 0;border-top:1px solid #E2E2DC}}.r:last-child{{border-bottom:1px solid #E2E2DC}}
.r i{{display:inline-block;font-style:normal;font-weight:800;font-size:20px;letter-spacing:.18em;text-transform:uppercase;background:#D2FF3C;padding:6px 10px 4px;margin-bottom:12px}}
.r b{{display:block;font-weight:800;font-size:{big}px;font-stretch:72%;line-height:.95;text-transform:uppercase}}
.r span{{display:block;font-size:26px;color:#5C5C57;margin-top:10px}}
.ft{{position:absolute;left:0;right:0;bottom:60px;display:flex;flex-direction:column;align-items:center;gap:16px}}
.ft img{{width:104px}}.ft div{{font-weight:600;font-size:21px;letter-spacing:.14em;text-transform:uppercase;color:#7A7A74}}</style>
<div class="top">{brand("Today's other deals")}</div><div class="rows">{"".join(rows)}</div>
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
