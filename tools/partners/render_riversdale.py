"""Render the Riversdale Fresh partner creatives for Sport Sport Sport.

Usage: python3 render.py <docket food photo dir> <output dir>
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

FOOD = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
ICON = (FOOD.parent / "riversdale-icon.svg").as_uri()

def photo(name):
    return (FOOD / name).as_uri()

BASE = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:%(w)dpx;height:%(h)dpx;overflow:hidden;font-family:"Inter Display","Inter",sans-serif;color:#1C211E;-webkit-font-smoothing:antialiased}
.wm{font-weight:900;letter-spacing:-.03em;color:#1C211E}
.icon{display:inline-flex;align-items:center;justify-content:center;background:#FFE58A;color:#1C211E;font-weight:900}
.ph{background-size:cover;background-position:center;overflow:hidden}
.tag{position:relative;background:#FFE58A;border-radius:22px;font-weight:800;text-transform:uppercase;letter-spacing:.12em}
.tag::before{content:"";position:absolute;border-radius:50%%;background:var(--hole)}
"""

def brand(size, icon):
    return (f'<div style="display:flex;align-items:center;gap:{int(size*.45)}px">'
            f'<img src="{ICON}" alt="" style="width:{icon}px;height:{icon}px;display:block">'
            f'<span class="wm" style="font-size:{size}px">Riversdale Fresh</span></div>')

CREATIVES = {
    # Article split feature: photo-led, 4:3.
    "split": (1200, 900, f"""
<div style="position:absolute;inset:0;background:#CFEBD8"></div>
<div class="ph" style="position:absolute;left:110px;top:110px;width:620px;height:620px;border-radius:56px;background-image:url('{photo('strip-prawn-noodles.jpg')}')"></div>
<div class="tag" style="--hole:#CFEBD8;position:absolute;left:640px;top:520px;width:460px;padding:44px 40px 40px 92px;transform:rotate(-6deg);box-shadow:0 18px 40px rgba(28,33,30,.12)">
  <span style="position:absolute;left:34px;top:50%;width:28px;height:28px;margin-top:-14px;border-radius:50%;background:#CFEBD8"></span>
  <div style="font-size:22px;color:#1F6B47">Supermarket prices</div>
  <div style="font-size:46px;letter-spacing:-.02em;text-transform:none;font-weight:900;margin-top:10px;line-height:1">Coles. Woolies. Aldi.</div>
</div>
<div style="position:absolute;left:110px;bottom:70px">{brand(40, 56)}</div>
"""),
    # Article full-width feature: 16:9, headline baked in.
    "wide": (1600, 900, f"""
<div style="position:absolute;inset:0;background:#F4F7F2"></div>
<div style="position:absolute;right:-120px;top:-60px;width:820px;height:820px;border-radius:50%;background:#CFEBD8"></div>
<div class="ph" style="position:absolute;right:300px;top:120px;width:440px;height:440px;border-radius:50%;background-image:url('{photo('strip-pesto-pasta.jpg')}');box-shadow:0 24px 60px rgba(28,33,30,.18)"></div>
<div class="ph" style="position:absolute;right:40px;top:300px;width:400px;height:400px;border-radius:50%;background-image:url('{photo('strip-tomato-salad.jpg')}');box-shadow:0 24px 60px rgba(28,33,30,.18)"></div>
<div class="ph" style="position:absolute;right:380px;top:560px;width:300px;height:300px;border-radius:50%;background-image:url('{photo('strip-rice-paper-rolls.jpg')}');box-shadow:0 24px 60px rgba(28,33,30,.18)"></div>
<div style="position:absolute;left:96px;top:96px">{brand(40, 56)}</div>
<h1 style="position:absolute;left:96px;top:250px;width:760px;font-size:112px;line-height:.98;letter-spacing:-.035em;font-weight:900;color:#1F6B47">Proper dinners, minus the meal kit markup.</h1>
<div style="position:absolute;left:96px;bottom:96px;background:#FFE58A;border-radius:999px;padding:22px 34px;font-size:30px;font-weight:800;letter-spacing:-.01em">This week's five picks are free</div>
"""),
    # Home page slot: wide 3:1, headline baked in.
    "home": (2400, 800, f"""
<div style="position:absolute;inset:0;background:#CFEBD8"></div>
<div style="position:absolute;left:110px;top:96px">{brand(44, 62)}</div>
<h1 style="position:absolute;left:110px;top:230px;width:1080px;font-size:132px;line-height:.96;letter-spacing:-.035em;font-weight:900;color:#1F6B47">Meal kit dinners. Supermarket prices.</h1>
<div style="position:absolute;left:110px;bottom:96px;font-size:34px;font-weight:700;color:#1C211E">Pick your dinners. Get a priced shopping list.</div>
<div style="position:absolute;right:110px;top:110px;display:flex;gap:36px">
  <div class="ph" style="width:340px;height:580px;border-radius:52px;background-image:url('{photo('strip-prawn-noodles.jpg')}')"></div>
  <div class="ph" style="width:340px;height:580px;border-radius:52px;background-image:url('{photo('strip-black-bean-bowl.jpg')}')"></div>
  <div class="ph" style="width:340px;height:580px;border-radius:52px;background-image:url('{photo('strip-pumpkin-soup.jpg')}')"></div>
</div>
<div class="tag" style="--hole:#CFEBD8;position:absolute;right:880px;bottom:70px;padding:30px 34px 28px 74px;transform:rotate(-5deg);box-shadow:0 18px 40px rgba(28,33,30,.14)">
  <span style="position:absolute;left:28px;top:50%;width:22px;height:22px;margin-top:-11px;border-radius:50%;background:#CFEBD8"></span>
  <span style="font-size:24px;color:#1F6B47">Free planner</span>
</div>
"""),
}
# Mobile crop of the home slot: 16:9, same message.
CREATIVES["home-mobile"] = (1600, 900, CREATIVES["wide"][2].replace(
    "Proper dinners, minus the meal kit markup.", "Meal kit dinners. Supermarket prices.").replace(
    "This week's five picks are free", "Free planner. Priced shopping list."))

with sync_playwright() as p:
    b = p.chromium.launch()
    for name, (w, h, body) in CREATIVES.items():
        pg = b.new_page(viewport={"width": w, "height": h})
        src = OUT / f"_{name}.html"
        src.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE % {'w': w, 'h': h}}</style></head><body>{body}</body></html>", encoding="utf-8")
        pg.goto(src.as_uri(), wait_until="load")
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / f"{name}.jpg"), type="jpeg", quality=86)
        print("rendered", name, w, h)
    b.close()
