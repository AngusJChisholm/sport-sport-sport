"""Render the two daily LinkedIn graphics (1080x1080) in the fixed house layout.

    python3 tools/linkedin_graphics.py spec.json out_dir

spec.json: {"date":"YYYY-MM-DD","headline_lines":["MONACO'S","SHIRT FOR","EUROPE","ONLY."],
 "highlight":"EUROPE","deal":"Brand x Property","descriptor":"Deal type",
 "others":[{"deal":"Brand x Property","sub":"Sport - deal type"}, ...]}
Optional "image": the lead's photo ("assets/..." file or an images.unsplash.com link,
same as its deals.json "image"). Slide 1 then sits on the photo; leave it out for plain black.
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

FIT = """async () => { await document.fonts.ready;
  for (const el of document.querySelectorAll('[data-fit]')) {
    const maxH = parseFloat(el.dataset.fit); let size = parseFloat(getComputedStyle(el).fontSize);
    while (size > 40 && (el.scrollHeight > maxH || el.scrollWidth > el.clientWidth + 2)) {
      size -= Math.max(0.5, size * 0.03); el.style.fontSize = size + 'px'; } } }"""

def club(deal):
    """Property colours from instagram/colours.json (used when there's no photo)."""
    prop = re.split(r"\s+[x\u00d7]\s+", deal or "", maxsplit=1)[-1].lower().strip()
    try:
        best = None
        for t in json.loads((ROOT / "instagram/colours.json").read_text())["teams"]:
            for n in t["names"]:
                if prop == n or (len(n) > 3 and re.search(rf"\b{re.escape(n)}\b", prop)):
                    if not best or len(n) > best[0]: best = (len(n), t["colours"][0])
        return best[1] if best else "#161616"
    except Exception:
        return "#161616"

def headline(s):
    hl = s.get("highlight", "").strip(".,!?' ").upper()
    return " ".join(f'<span class="v">{e(w)}</span>' if w.strip(".,!?' ").upper() == hl and hl else e(w)
                    for w in " ".join(s["headline_lines"]).split())

def slide1(s):
    """Photo-led cover (Front Office Sports style): full-bleed photo, fade to black, centred text in the bottom third."""
    src = photo(s.get("image"))
    if src:
        top = f'<div class="ph" style="background-image:url(\'{src}\')"></div>'
    else:  # no photo: property colour with the pairing set large up top
        top = (f'<div class="ph" style="background:{club(s["deal"])}"></div>'
               f'<div class="big">{e(s["deal"]).replace(" x ", " &times; ")}</div>')
    pair = e(s['deal']).replace(' x ', ' &times; ')
    return f"""<style>{css()}
.ph{{position:absolute;inset:0;background-position:center 25%;background-size:cover}}
.fade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0) 48%,rgba(0,0,0,.75) 64%,#000 76%,#000 100%)}}
.big{{position:absolute;left:72px;right:72px;top:120px;text-align:center;font-weight:800;font-size:110px;font-stretch:72%;line-height:.92;text-transform:uppercase;color:rgba(255,255,255,.95)}}
.low{{position:absolute;left:64px;right:64px;bottom:58px;display:flex;flex-direction:column;align-items:center;text-align:center}}
.brand{{font-weight:800;font-size:24px;letter-spacing:.14em;text-transform:uppercase;font-stretch:90%}}
.brand span{{color:#D2FF3C}}
.h{{width:100%;margin-top:14px;font-weight:800;font-size:104px;font-stretch:68%;line-height:.9;text-transform:uppercase;letter-spacing:-.005em}}
.meta{{margin-top:20px;font-weight:600;font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:#BDBDBD}}
.meta b{{color:#fff;font-weight:800}}</style>
{top}<div class="fade"></div>
<div class="low"><div class="brand">Sport Sport Sport <span>/ Deal of the day</span></div>
<div class="h" data-fit="200">{headline(s)}</div>
<div class="meta">{('<b>' + pair + '</b> &middot; ') if src else ''}{e(s['descriptor'])}</div></div>"""

def slide2(s):
    """White slide (matches the website round-up). Volt is a fill behind black type, never text on white."""
    rows = "".join(f'<div class="r"><b>{e(o["deal"])}</b><span>{e(o["sub"])}</span></div>' for o in s["others"][:5])
    return f"""<style>{css()}
body{{background:#fff;color:#000}}
.lab{{background:#D2FF3C;color:#000;padding:10px 14px 8px;top:86px;left:97px}}
.rows{{position:absolute;left:97px;right:96px;top:180px;border-top:2px solid #000}}
.r{{padding:27px 0 30px;border-bottom:1px solid #DEDED8}}.r:last-child{{border-bottom:0}}
.r b{{display:block;font-weight:800;font-size:47px;font-stretch:96%;line-height:52px;text-transform:uppercase}}
.r span{{display:block;font-weight:400;font-size:27.5px;color:#5C5C57;margin-top:14px}}</style>
<div class="lab">Today's other deals</div><div class="rows">{rows}</div>
<img class="wm" src="data:image/svg+xml;base64,{wordmark('black')}">"""

def render(spec, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1080})
        for n, h in (("slide1", slide1(spec)), ("slide2", slide2(spec))):
            pg.set_content(h, wait_until="networkidle"); pg.evaluate(FIT)
            assert pg.evaluate('document.fonts.check("800 50px Archivo")')
            pg.screenshot(path=str(out / f"sss-{spec['date']}-{n}.png"))
        b.close()

if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
