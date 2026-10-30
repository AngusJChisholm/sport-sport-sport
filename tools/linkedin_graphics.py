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

def slide1(s):
    src = photo(s.get("image"))
    bg = (f'<div style="position:absolute;inset:0;background:url(\'{src}\') center/cover"></div>'
          '<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.6) 0%,rgba(0,0,0,.3) 22%,rgba(0,0,0,.55) 45%,rgba(0,0,0,.9) 100%)"></div>') if src else ""
    lines = "".join(
        f'<div class="{"v" if l.strip(".,!?' ").upper()==s.get("highlight","").strip(".,!?' ").upper() else ""}">{e(l)}</div>'
        for l in s["headline_lines"])
    return f"""<style>{css()}
.h{{position:absolute;left:94px;right:97px;top:256px;font-weight:800;font-size:140px;font-stretch:94%;line-height:127px;text-transform:uppercase;letter-spacing:-.005em}}
.d{{position:absolute;left:97px;bottom:100px;font-weight:500;font-size:28px;line-height:43px;letter-spacing:.13em;text-transform:uppercase;max-width:700px}}</style>
{bg}<div class="lab">Deal of the day</div><div class="h">{lines}</div>
<div class="d">{e(s['deal'])}<br>{e(s['descriptor'])}</div>
<img class="wm" src="data:image/svg+xml;base64,{wordmark()}">"""

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
            pg.set_content(h, wait_until="networkidle"); pg.evaluate("document.fonts.ready")
            assert pg.evaluate('document.fonts.check("800 50px Archivo")')
            pg.screenshot(path=str(out / f"sss-{spec['date']}-{n}.png"))
        b.close()

if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
