"""Contact sheet of every article photo, to eyeball them in one go (run on GitHub, which can load Unsplash).

    python3 tools/photo_sheet.py   ->  ig/_photos/sheet-N.jpg
"""
import html, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from instagram_render import photo_src
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
deals = [d for d in json.loads((ROOT / "deals.json").read_text())["deals"] if d.get("image") and d.get("article")]
out = ROOT / "ig" / "_photos"
out.mkdir(parents=True, exist_ok=True)
for old in out.glob("*.jpg"):
    old.unlink()
PER = 12
with sync_playwright() as p:
    b = p.chromium.launch()
    for n in range(0, len(deals), PER):
        cells = "".join(
            f'<figure><div style="background-image:url(\'{photo_src(d["image"], 600)}\')"></div>'
            f'<figcaption>{html.escape(d["deal"])}</figcaption></figure>' for d in deals[n:n + PER])
        doc = f"""<html><body style="margin:0;background:#111;color:#fff;font:600 20px Arial;display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:12px;width:1600px">
<style>figure{{margin:0}}figure div{{height:240px;background:#333 center/cover}}figcaption{{padding:6px 2px}}</style>{cells}</body></html>"""
        pg = b.new_page(viewport={"width": 1624, "height": 900})
        pg.set_content(doc, wait_until="networkidle")
        pg.screenshot(path=str(out / f"sheet-{n // PER + 1}.jpg"), type="jpeg", quality=80, full_page=True)
        pg.close()
    b.close()
print("sheets written")
