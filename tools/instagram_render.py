"""Render a day's Instagram carousel and story frames as JPEGs.

Reads instagram/queue/<date>.json and writes ig/<date>/feed-N.jpg,
ig/<date>/story-N.jpg and ig/<date>/manifest.json.
Needs: pip install playwright && playwright install --with-deps chromium

    python3 tools/instagram_render.py 2026-10-14
"""
import html
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
MEL = ZoneInfo("Australia/Melbourne")
VOLT = "#D2FF3C"
SITE_LABEL = "Full archive - link in bio"

FEED_W, FEED_H = 1080, 1350
STORY_W, STORY_H = 1080, 1920
RENDER_STORIES = False  # Angus switched off stories and Reels
RENDER_REELS = False


def esc(s):
    return html.escape(str(s or ""), quote=True)


def wordmark(colour):
    name = "wordmark-black.svg" if colour == "black" else "wordmark-white.svg"
    svg = (ROOT / "assets" / name).read_text()
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg).strip()
    return svg.replace("<svg ", '<svg class="wm" aria-label="Sport Sport Sport" role="img" ', 1)


BASE_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:'Archivo','Helvetica Neue',Helvetica,Arial,sans-serif;font-weight:500;-webkit-font-smoothing:antialiased}
.frame{position:relative;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between}
.disp{font-weight:800;text-transform:uppercase;letter-spacing:-.045em;line-height:.86;margin:0;transform:scaleX(.92);transform-origin:left top;width:108.7%;overflow-wrap:normal}
.tag{align-self:flex-start;font-weight:800;font-size:24px;letter-spacing:.14em;text-transform:uppercase;padding:12px 16px 10px;border:2px solid currentColor;line-height:1}
.lbl{font-weight:800;font-size:24px;letter-spacing:.18em;text-transform:uppercase}
.sup{font-weight:500;font-size:30px;letter-spacing:.12em;text-transform:uppercase;line-height:1.4}
.rows{border-top:2px solid currentColor;display:flex;flex-direction:column;font-size:16px}
.row{padding:1.6em 0;border-bottom:1px solid var(--line)}
.row b{display:block;font-weight:800;font-size:2.5em;text-transform:uppercase;letter-spacing:-.03em;line-height:1.05}
.row span{display:block;font-size:1.625em;color:var(--muted);margin-top:.3em;line-height:1.35}
.top{display:flex;justify-content:space-between;align-items:center}
.foot{display:flex;justify-content:space-between;align-items:flex-end}
.wm{width:128px;height:auto;display:block}
.v{color:#D2FF3C}
"""

FIT_JS = """
async () => {
  await document.fonts.ready;
  for (const el of document.querySelectorAll('[data-fit]')) {
    const maxH = parseFloat(el.dataset.fit);
    let size = parseFloat(getComputedStyle(el).fontSize);
    const min = parseFloat(el.dataset.min || '48');
    while (size > min && (el.scrollHeight > maxH || el.scrollWidth > el.clientWidth + 2)) {
      size -= Math.max(0.5, size * 0.04);
      el.style.fontSize = size + 'px';
    }
  }
}
"""


def page(body, w, h, bg, fg, extra_css=""):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;800&display=swap" rel="stylesheet">
<style>{BASE_CSS}{PHOTO_CSS}
body{{width:{w}px;height:{h}px;background:{bg};color:{fg}}}
.frame{{width:{w}px;height:{h}px}}
{extra_css}</style></head><body>{body}</body></html>"""


def highlight(text, word):
    """Escape text and wrap the first match of word in the volt accent."""
    t = esc(text)
    if not word:
        return t
    w = esc(word)
    i = t.lower().find(w.lower())
    if i < 0:
        return t
    return t[:i] + f'<span class="v">{t[i:i+len(w)]}</span>' + t[i+len(w):]


def counter(n, total):
    return f'<div class="lbl mute">{n} / {total}</div>'


SWIPE = ('<div class="lbl" style="display:flex;align-items:center;gap:16px">Swipe'
         '<svg width="44" height="24" viewBox="0 0 44 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true">'
         '<path d="M0 12h40M30 2l10 10-10 10"/></svg></div>')

FEED_CSS = ".frame{padding:88px;--line:#292929;--muted:#9E9E9E}" + """
/* Inner slides: a club-colour edge and big numbered rows. Only slide 1 has the photo. */
.edge{position:absolute;left:0;top:0;bottom:0;width:16px;z-index:3}
.frame>.top,.frame>.mid,.frame>.foot{position:relative;z-index:1}
.mid{display:flex;flex-direction:column;gap:44px}
.nrows{border-top:3px solid #FFFFFF;display:flex;flex-direction:column;font-size:21px}
.nrow{display:grid;grid-template-columns:5.6em 1fr;padding:2em 0;border-bottom:1px solid #333}
.nrow .n{font-weight:800;font-size:2.75em;color:#D2FF3C;letter-spacing:-.02em;line-height:1;padding-top:.08em}
.nrow b{display:block;font-weight:800;font-size:3.5em;text-transform:uppercase;letter-spacing:-.03em;line-height:1}
.nrow span{display:block;font-size:2em;color:#C8C8C8;margin-top:.45em;line-height:1.3}
.orow{display:grid;grid-template-columns:1fr auto;gap:1.6em;align-items:center;padding:1.5em 0;border-bottom:1px solid #333}
.orow .s{display:block;font-weight:800;font-size:1.4em;letter-spacing:.16em;text-transform:uppercase;color:#D2FF3C;margin-bottom:.45em}
.orow b{display:block;font-weight:800;font-size:3em;text-transform:uppercase;letter-spacing:-.03em;line-height:1}
.orow span.x{display:block;font-size:1.75em;color:#C8C8C8;margin-top:.35em;line-height:1.3}
.title-xl{font-size:150px}
.frame>.edge{position:absolute!important;z-index:3!important}
.mute{color:#9E9E9E}
/* White inner slides (match the website). Volt is only ever a fill behind black type on white. */
.frame.light{background:#FFFFFF;color:#000000;--line:#DEDED8;--muted:#5C5C57}
.light .mute{color:#5C5C57}
.light .nrows{border-top-color:#000000}
.light .nrow,.light .orow{border-bottom-color:#DEDED8}
.light .nrow .n{color:#000000}
.light .nrow span,.light .orow span.x{color:#5C5C57}
.light .orow .s{display:inline-block;background:#D2FF3C;color:#000000;padding:.35em .55em .25em}
.light .v{color:#000000;background:#D2FF3C;padding:0 .06em;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.light .edge.pale{border-right:3px solid #000000}

"""


# ---------- feed slides (slide 1 black/photo, inner slides white) ----------

COVER_CSS = """
.frame.cover{padding:0!important;display:block}
.cover>.cv-ph,.cover>.cv-fade,.cover>.cv-big,.cover>.cv-reg,.cover>.cv-low{position:absolute!important}
.cv-ph{position:absolute;inset:0;background-position:center 25%;background-size:cover;z-index:0}
.cv-fade{position:absolute;inset:0;z-index:1;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 12%,rgba(0,0,0,0) 50%,rgba(0,0,0,.75) 64%,#000 76%,#000 100%)}
.cv-big{position:absolute;left:80px;right:80px;top:170px;text-align:center;font-weight:800;font-size:150px;font-stretch:72%;line-height:.9;text-transform:uppercase;color:rgba(255,255,255,.95);z-index:2}
.cv-reg{position:absolute;right:64px;top:64px;font-weight:800;font-size:22px;letter-spacing:.18em;text-transform:uppercase;color:#fff;text-shadow:0 1px 10px rgba(0,0,0,.5);z-index:2}
.cv-low{position:absolute;left:64px;right:64px;bottom:64px;display:flex;flex-direction:column;align-items:center;text-align:center;z-index:2}
.cv-brand{font-weight:800;font-size:28px;letter-spacing:.14em;text-transform:uppercase;font-stretch:90%}
.cv-brand span{color:#D2FF3C}
.cv-h{width:100%;margin:16px 0 0;font-weight:800;font-size:128px;font-stretch:68%;text-transform:uppercase;line-height:.9;letter-spacing:-.005em}
.cv-meta{margin-top:22px;font-weight:600;font-size:24px;letter-spacing:.14em;text-transform:uppercase;color:#BDBDBD}
.cv-meta b{color:#fff;font-weight:800}
.cv-swipe{margin-top:26px;background:#fff;color:#000;font-weight:800;font-size:24px;letter-spacing:.12em;text-transform:uppercase;padding:9px 14px 7px;line-height:1}
"""


COVER_CSS += """
/* Cover fading to white */
.cover.cl .cv-fade{background:linear-gradient(180deg,rgba(0,0,0,.25) 0%,rgba(0,0,0,0) 10%,rgba(255,255,255,0) 60%,rgba(255,255,255,.88) 71%,#fff 79%,#fff 100%)}
.cover.cl .cv-ph{background-position:center 35%}
.cover.cl .cv-low{color:#000}
.cover.cl .cv-brand span{color:#000;background:#D2FF3C;padding:.1em .3em 0}
.cover.cl .cv-h .v{color:#000;background:#D2FF3C;padding:0 .06em}
.cover.cl .cv-meta{color:#5C5C57}
.cover.cl .cv-meta b{color:#000}
.cover.cl .cv-swipe{background:#000;color:#fff}
"""


def feed_cover(c):
    """Photo-led cover (Front Office Sports style): full-bleed photo, fade to black, centred text in the bottom third."""
    src = photo_src(deal_image(c), FEED_W) if (c.get("image") or c.get("deal")) else ""
    deal = esc(c.get("deal", ""))
    pair = re.sub(r"\s+x\s+", " &times; ", deal, count=1)
    if src:
        top = f'<div class="cv-ph" style="background-image:url(\'{src}\')"></div>'
    else:  # no photo: property colour with the pairing set large up top
        bg = club_colours({"deal": c.get("deal", ""), "colours": c.get("colours")})[0] if c.get("deal") else "#161616"
        bg = "#161616" if bg == VOLT else bg
        if COVER_LIGHT:  # white house look: no black block, the pairing set large in black up top
            top = '<style>.cover.cl.np .cv-fade{display:none}.cover.cl.np .cv-reg{color:#7A7A74;text-shadow:none}.cover.cl.np .cv-low{top:64px;justify-content:center}.cover.cl.np .cv-h{font-size:170px}.cover.cl.np .cv-meta{margin-top:30px;font-size:26px}</style><div class="cv-ph" style="background:#fff"></div>'
        else:
            top = f'<div class="cv-ph" style="background:{bg}"></div>' + (f'<div class="cv-big">{pair}</div>' if deal else "")
    meta = (f'<b>{pair}</b> &middot; ' if src and deal else "") + esc(c.get("descriptor", ""))
    return f"""<style>{COVER_CSS}</style><div class="frame cover{' cl' if COVER_LIGHT else ''}{'' if src else ' np'}" style="background:{'#fff' if COVER_LIGHT else '#000'}">{top}<div class="cv-fade"></div>
<div class="cv-reg">{esc(c.get('region',''))}</div>
<div class="cv-low">
<h1 class="cv-h" data-fit="{240 if src else 560}" data-min="56">{highlight(c['headline'], c.get('highlight'))}</h1>
<div class="cv-meta">{meta}</div>
<div class="cv-swipe">Swipe &raquo;</div></div>
</div>"""


def edge_bar(colour):
    """Retired: inner slides now follow the cover design (black, centred), no club-colour edge."""
    return ""


# ---------- inner slides: same look as the cover ----------
# Black background, centred condensed type, volt accents, white pill, white wordmark.
DARK_CSS = """
.frame.dk{background:#000;color:#fff;padding:64px!important;display:flex;flex-direction:column;align-items:center;text-align:center}
.dk .d-bg{position:absolute!important;inset:-80px;z-index:0!important;background-position:center;background-size:cover;filter:blur(48px) saturate(1.15) brightness(.32)}
.dk .d-bg::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.25),rgba(0,0,0,.55))}
.frame.dk{position:relative;overflow:hidden}
.dk>*:not(.d-bg){position:relative;z-index:1}
.dk .d-top{width:100%;display:flex;justify-content:center;position:relative}
.dk .d-brand{font-weight:800;font-size:28px;letter-spacing:.14em;text-transform:uppercase;font-stretch:90%}
.dk .d-brand span{color:#D2FF3C}
.dk .d-n{position:absolute;right:0;top:0;font-weight:800;font-size:22px;letter-spacing:.18em;color:#8A8A8A}
.dk .d-mid{flex:1;width:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:34px}
.dk .d-h{width:100%;margin:0;font-weight:800;font-size:112px;font-stretch:68%;text-transform:uppercase;line-height:.9;letter-spacing:-.005em}
.dk .d-rule{width:120px;height:4px;background:#D2FF3C}
.dk .d-rows{width:100%;display:flex;flex-direction:column;font-size:20px}
.dk .d-row{padding:1.25em 0;border-top:1px solid #2A2A2A}
.dk .d-row:last-child{border-bottom:1px solid #2A2A2A}
.dk .d-row .n{display:block;font-weight:800;font-size:1.3em;letter-spacing:.18em;text-transform:uppercase;color:#D2FF3C;margin-bottom:.35em}
.dk .d-row b{display:block;font-weight:800;font-size:3.2em;font-stretch:72%;text-transform:uppercase;line-height:.95}
.dk .d-row span.x{display:block;font-size:1.5em;color:#BDBDBD;margin-top:.4em;line-height:1.3;letter-spacing:.02em}
.dk .d-foot{width:100%;display:flex;flex-direction:column;align-items:center;gap:18px}
.dk .d-foot .wm{width:110px}
.dk .d-meta{font-weight:600;font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:#8A8A8A}
.dk .d-pill{background:#fff;color:#000;font-weight:800;font-size:26px;letter-spacing:.12em;text-transform:uppercase;padding:12px 18px 10px;line-height:1}
.dk .d-big{font-weight:800;font-size:200px;font-stretch:68%;text-transform:uppercase;line-height:.88;margin:0}
.dk .d-sup{font-weight:600;font-size:26px;letter-spacing:.14em;text-transform:uppercase;color:#BDBDBD}
.frame.dk.wk{padding:0!important;display:block}
.wk>.cv-ph,.wk>.cv-fade{position:absolute!important}
.wk .d-top{position:absolute!important;left:64px;right:64px;top:64px;z-index:2;text-shadow:0 1px 10px rgba(0,0,0,.5)}
.wk .d-low{position:absolute!important;left:64px;right:64px;bottom:64px;z-index:2;display:flex;flex-direction:column;align-items:center;gap:20px}
.wk .d-num{font-weight:800;font-size:150px;font-stretch:68%;line-height:.85;color:#D2FF3C}
.wk.nophoto .d-low{top:200px;justify-content:center}
"""
DARK_CSS += """
/* White theme for inner slides. Volt is only ever a fill behind black type on white. */
.frame.dk.lt{background:#fff;color:#000}
.lt .d-brand span{color:#000;background:#D2FF3C;padding:.1em .3em 0}
.lt .d-rule{background:#000}
.lt .d-row{border-top-color:#E2E2DC}
.lt .d-row:last-child{border-bottom-color:#E2E2DC}
.lt .d-row .n{color:#000}
.lt .d-row .n.s{display:inline-block;background:#D2FF3C;padding:.3em .5em .2em}
.lt .d-row span.x,.lt .d-sup{color:#5C5C57}
.lt .d-meta{color:#7A7A74}
.lt .d-pill{background:#000;color:#fff}
.lt .v{color:#000;background:#D2FF3C;padding:0 .06em;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.lt .d-num{color:#000}
.wk.lt .cv-fade{background:linear-gradient(180deg,rgba(255,255,255,0) 0%,rgba(255,255,255,0) 52%,rgba(255,255,255,.88) 64%,#fff 73%,#fff 100%)}
.wk.lt .d-top{text-shadow:none}
.wk.lt .d-top .d-brand{color:#fff;text-shadow:0 1px 3px rgba(0,0,0,.7),0 0 18px rgba(0,0,0,.55)}
.wk.lt.nophoto .d-top .d-brand{color:#000;text-shadow:none}
"""



INNER_BG = False  # set True to put the lead photo, blurred and darkened, behind inner slides
LIGHT = True      # inner slides: white background (Angus is moving SSS to white)
COVER_LIGHT = True   # cover fades to white (Angus, 2 Nov 2026: SSS is moving to white)
_BG_SRC = ""


def dk_bg():
    return f'<div class="d-bg" style="background-image:url(\'{_BG_SRC}\')"></div>' if INNER_BG and _BG_SRC else ""


def dk_top(label, n, total, bg=True):
    """No section labels on the slides any more (Angus, 2 Nov 2026): headlines only."""
    return dk_bg() if bg else ""


def dk_foot(text, n=None, total=None):
    count = f"{n} / {total}" + (" &middot; " if text else "") if n else ""
    return f'<div class="d-foot">{wordmark("black" if LIGHT else "white")}<div class="d-meta">{count}{esc(text)}</div></div>'


def rows_slide(label, title, rows, n, total, footer_right="", edge=None):
    """Inner slide in the cover style: centred title, volt rule, numbered rows."""
    rows_html = "".join(
        f'<div class="d-row"><span class="n">{i:02d}</span><b>{esc(r.get("main"))}</b>'
        + (f'<span class="x">{esc(r.get("sub"))}</span>' if r.get("sub") else "") + "</div>"
        for i, r in enumerate(rows, 1))
    title_html = f'<h2 class="d-h" data-fit="300" data-min="56">{esc(title)}</h2><div class="d-rule"></div>' if title else ""
    return f"""<style>{DARK_CSS}</style><div class="frame dk{' lt' if LIGHT else ''}">{dk_top(label, n, total)}
<div class="d-mid">{title_html}<div class="d-rows" data-fit="{640 if title else 900}" data-min="9">{rows_html}</div></div>
{dk_foot(footer_right, n, total)}</div>"""


def others_slide(others, n, total, edge=None):
    """Round-up slide in the cover style: sport in volt, pairing, deal type."""
    rows = []
    for o in others[:5]:
        sub = str(o.get("sub") or "")
        sport, _, rest = sub.partition(" - ")
        if not rest:
            sport, rest = "", sub
        rows.append('<div class="d-row">' + (f'<span class="n s">{esc(sport)}</span>' if sport else "")
                    + f'<b>{esc(o["deal"])}</b>' + (f'<span class="x">{esc(rest)}</span>' if rest else "") + "</div>")
    return f"""<style>{DARK_CSS}</style><div class="frame dk{' lt' if LIGHT else ''}">{dk_top("Today's other deals", n, total)}
<div class="d-mid"><h2 class="d-h">Recent deals.</h2><div class="d-rule"></div><div class="d-rows" data-fit="760" data-min="8" style="font-size:21px">{"".join(rows)}</div></div>
{dk_foot(SITE_LABEL, n, total)}</div>"""


def lead_edge(cover):
    return None


def feed_rows_slide(label, title, rows, n, total, footer_right=""):
    return rows_slide(label, title, rows, n, total, footer_right)


def feed_close(n, total):
    return f"""<style>{DARK_CSS}</style><div class="frame dk{' lt' if LIGHT else ''}">{dk_top("Follow", n, total)}
<div class="d-mid"><h2 class="d-big">All things <span class="v">sport</span> business.</h2>
<div class="d-sup">Global &amp; ANZ deals, every weekday</div><div class="d-pill">Follow for daily deals</div></div>
{dk_foot(SITE_LABEL, n, total)}</div>"""


def week_item(item, idx, n, total, label="The week in deals"):
    """Week and evergreen slides: the cover layout, with the deal's photo when it has one."""
    src = photo_src(deal_image(item), FEED_W)
    top = (f'<div class="cv-ph" style="background-image:url(\'{src}\')"></div><div class="cv-fade"></div>') if src else ""
    return f"""<style>{COVER_CSS}{DARK_CSS}</style><div class="frame dk wk{' lt' if LIGHT else ''}{'' if src else ' nophoto'}">{top}{dk_top(label, n, total, bg=not src)}
<div class="d-low"><div class="d-num">{idx:02d}</div>
<h2 class="d-h" data-fit="300" data-min="56" style="font-size:118px">{esc(item['deal'])}</h2>
<div class="d-sup" style="text-transform:none;letter-spacing:.02em;font-size:30px;line-height:1.35">{esc(item.get('sub',''))}</div>
<div class="d-meta">{n} / {total}{' &middot; ' + esc(item['sport']) if item.get('sport') else ''}</div></div></div>"""


# ---------- photos ----------
# A deal's photo comes from the queue item's own "image", else the matching deal in deals.json.
# Local files (assets/...) are embedded; Unsplash links are sized for the slide.
PHOTO_CSS = """
.ph{position:absolute;inset:0;background-position:center;background-size:cover;z-index:0}
.ph::after{content:"";position:absolute;inset:0;background:var(--shade)}
.frame>*:not(.ph):not(.bar){position:relative;z-index:1}
.photo .lbl[style*="9E9E9E"],.photo [style*="9E9E9E"]{color:rgba(255,255,255,.88)!important}
.photo .disp,.photo .sup,.photo .row b{text-shadow:0 2px 18px rgba(0,0,0,.35)}
.photo .foot{border-top-color:rgba(255,255,255,.3)!important}
"""
SHADE_FEED = "linear-gradient(180deg,rgba(0,0,0,.62) 0%,rgba(0,0,0,.22) 30%,rgba(0,0,0,.5) 55%,rgba(0,0,0,.9) 100%)"
SHADE_STORY = "linear-gradient(180deg,rgba(0,0,0,.6) 0%,rgba(0,0,0,.25) 25%,rgba(0,0,0,.55) 50%,rgba(0,0,0,.92) 100%)"
_DEALS = None


def deal_key(name):
    parts = re.split(r"\s+[x\u00d7]\s+", name or "", maxsplit=1)
    return tuple(norm(x) for x in parts)


def deal_image(item):
    if item.get("image"):
        return item["image"]
    global _DEALS
    if _DEALS is None:
        try:
            _DEALS = {deal_key(d.get("deal")): d.get("image") for d in json.loads((ROOT / "deals.json").read_text())["deals"] if d.get("image")}
        except Exception:
            _DEALS = {}
    return _DEALS.get(deal_key(item.get("deal")))


def photo_src(img, w):
    import base64
    img = str(img or "")
    if re.fullmatch(r"assets/[\w/.-]+\.(jpe?g|png|webp)", img) and (ROOT / img).exists():
        mime = "image/png" if img.endswith(".png") else "image/webp" if img.endswith(".webp") else "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode((ROOT / img).read_bytes()).decode()
    m = re.match(r"^https://images\.unsplash\.com/(photo-[\w-]+)", img)
    if m:
        local = ROOT / "assets" / "img" / "u" / f"{m.group(1)}.jpg"
        if local.exists():
            return "data:image/jpeg;base64," + base64.b64encode(local.read_bytes()).decode()
        return f"https://images.unsplash.com/{m.group(1)}?w={w}&q=80&auto=format&fit=crop"
    return ""


def photo_layer(img, w, shade):
    src = photo_src(img, w)
    return f'<div class="ph" style="background-image:url(\'{src}\');--shade:{shade}"></div>' if src else ""


def feature_image(date):
    """The weekend feature's article photo (features.json), so slide 1 always matches the article."""
    try:
        for f in json.loads((ROOT / "features.json").read_text()).get("features", []):
            if f.get("date") == date and f.get("image"):
                return f["image"]
    except Exception:
        pass
    return None


def build_feed(feed):
    global _BG_SRC
    c = feed.get("cover") or {}
    _BG_SRC = photo_src(feed.get("image") or deal_image(c), 400) if (c or feed.get("image")) else ""
    slides = []
    if feed.get("kind") == "week":
        items = feed["items"][:8]
        total = len(items) + 2
        if feed.get("image"):
            # Photo-led week cover: today's lead photo, with its pairing named in the meta line.
            slides.append(feed_cover({"tag": "Week in deals", "region": feed.get("region", "Global & ANZ"),
                                      "headline": feed.get("headline", "The week in deals."),
                                      "highlight": feed.get("highlight", "week"),
                                      "image": feed["image"], "deal": feed.get("deal", ""),
                                      "descriptor": feed.get("descriptor", "The biggest deals this week")}))
        else:
            slides.append(feed_cover({"tag": "Week in deals", "region": feed.get("region", "Global & ANZ"),
                                      "headline": feed.get("headline", "The week in deals."),
                                      "highlight": feed.get("highlight", "week"),
                                      "deal": feed.get("descriptor", "The biggest deals this week")}))
        for i, it in enumerate(items, 1):
            slides.append(week_item(it, i, i + 1, total))
        slides.append(feed_close(total, total))
        return slides

    if feed.get("kind") == "feature":
        # Weekend feature: cover, 2-4 point slides, close. The Reel is made from these slides as usual.
        body = feed.get("slides", [])[:4]
        total = len(body) + 2
        cover = dict(feed["cover"])
        cover.setdefault("tag", "Weekend feature")
        slides.append(feed_cover(cover))
        for n, sl in enumerate(body, 2):
            rows = [{"main": x} if isinstance(x, str) else x for x in sl.get("rows", [])][:3]
            slides.append(rows_slide(sl.get("label", "The feature"), sl.get("title"), rows, n, total,
                                     "Full feature - link in bio", VOLT))
        slides.append(feed_close(total, total))
        return slides

    parts = ["cover", "deal"]
    if feed.get("why"):
        parts.append("why")
    if feed.get("others"):
        parts.append("others")
    parts.append("close")
    total = len(parts)
    edge = lead_edge(feed["cover"])
    for n, p in enumerate(parts, 1):
        if p == "cover":
            slides.append(feed_cover(feed["cover"]))
        elif p == "deal":
            d = feed["deal"]
            slides.append(rows_slide("The deal", d.get("title"), d["rows"][:3], n, total, SITE_LABEL, edge))
        elif p == "why":
            w = feed["why"]
            rows = [{"main": x} if isinstance(x, str) else x for x in w.get("points", [])][:3]
            slides.append(rows_slide("Why it matters", w.get("title"), rows, n, total, SITE_LABEL, edge))
        elif p == "others":
            slides.append(others_slide(feed["others"], n, total, edge))
        else:
            slides.append(feed_close(n, total))
    return slides


def build_evergreen(ev):
    """Weekly evergreen carousel: cover, one numbered slide per item, close."""
    global _BG_SRC
    _BG_SRC = ""
    items = ev["items"][:8]
    total = len(items) + 2
    label = ev.get("label", "The breakdown")
    slides = [feed_cover({"tag": label, "region": ev.get("region", ""),
                          "headline": ev["headline"], "highlight": ev.get("highlight"),
                          "deal": ev.get("descriptor", "")})]
    for i, it in enumerate(items, 1):
        slides.append(week_item({"deal": it["title"], "sub": it.get("sub", ""), "sport": it.get("tag", "")},
                                i, i + 1, total, label))
    slides.append(feed_close(total, total))
    return slides


# ---------- reel (motion video from the carousel) ----------

def make_reel(images, out_path, per=3.2, fade=0.4):
    """Slides centred on a 9:16 black frame, slow push-in, crossfades, silent audio track."""
    import subprocess
    fps = 30
    n = len(images)
    total = n * per - (n - 1) * fade
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for img in images:
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{per}", "-i", str(img)]
    cmd += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]
    frames = int(per * fps)
    parts = []
    for i in range(n):
        parts.append(
            f"[{i}:v]scale=1080:1350,pad=1080:1920:0:285:black,scale=2160:3840,"
            f"zoompan=z='1+0.035*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={fps},"
            f"setsar=1,format=yuv420p[v{i}]")
    last = "v0"
    for i in range(1, n):
        off = i * (per - fade)
        parts.append(f"[{last}][v{i}]xfade=transition=fade:duration={fade}:offset={off:.2f}[x{i}]")
        last = f"x{i}"
    cmd += ["-filter_complex", ";".join(parts), "-map", f"[{last}]", "-map", f"{n}:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(fps),
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out_path)]
    subprocess.run(cmd, check=True)


def prune(keep_days=21):
    """Drop image folders older than keep_days so the repo and site stay small."""
    import shutil
    from datetime import date as _d, timedelta
    cutoff = _d.today() - timedelta(days=keep_days)
    for d in (ROOT / "ig").glob("20*-*-*"):
        try:
            if _d.fromisoformat(d.name) < cutoff:
                shutil.rmtree(d)
        except ValueError:
            pass


# ---------- story frames (club colours) ----------

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
FALLBACK = [VOLT, "#000000"]  # brand volt when a property's colours are unknown


def club_colours(item):
    """Story colours: the queue's own "colours" first, then instagram/colours.json, then brand volt."""
    own = item.get("colours")
    if isinstance(own, list) and own and all(HEX.match(str(c)) for c in own):
        return [own[0], own[1] if len(own) > 1 else own[0]]
    table = json.loads((ROOT / "instagram" / "colours.json").read_text())["teams"]
    prop = item.get("property") or re.split(r"\s+[x×]\s+", item.get("deal", ""), maxsplit=1)[-1]
    p = norm(prop)
    best = None
    for t in table:
        for name in t["names"]:
            n = norm(name)
            if p == n or (len(n) > 3 and re.search(rf"\b{re.escape(n)}\b", p)):
                if not best or len(n) > best[0]:
                    best = (len(n), t["colours"])
    return best[1] if best else FALLBACK


def luminance(hex_colour):
    h = hex_colour.lstrip("#")
    rgb = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def story(item):
    primary, secondary = club_colours(item)
    light = luminance(primary) > 0.35
    fg = "#000000" if light else "#FFFFFF"
    line = "rgba(0,0,0,.3)" if light else "rgba(255,255,255,.35)"
    btn_bg, btn_fg = ("#000000", "#FFFFFF") if light else ("#FFFFFF", "#000000")
    points = item.get("points", [])[:3]
    rows = "".join(f'<div class="row"><b>{esc(p)}</b></div>' for p in points)
    ph = photo_layer(deal_image(item), STORY_W, SHADE_STORY)
    if ph:  # photo story: white type over the photo, club colour kept as the edge bar
        light, fg, line = False, "#FFFFFF", "rgba(255,255,255,.35)"
        btn_bg, btn_fg = "#FFFFFF", "#000000"
        secondary = primary if luminance(primary) > 0.03 else secondary
    body = f"""<div class="frame{' photo' if ph else ''}" style="padding:220px 88px 260px">{ph}
<div class="bar" style="position:absolute;top:0;bottom:0;left:0;width:40px;background:{secondary};z-index:2"></div>
<div class="tag">{esc(item.get('tag') or 'Deal of the day')}</div>
<div style="display:flex;flex-direction:column;gap:56px">
<h1 class="disp" data-fit="520" style="font-size:190px">{esc(item['deal'])}</h1>
<div class="rows" data-fit="560" data-min="9">{rows}</div>
</div>
<div class="foot">{wordmark('black' if light else 'white').replace('class="wm"', 'class="wm" style="width:140px"')}
<div style="background:{btn_bg};color:{btn_fg};font-weight:800;font-size:26px;letter-spacing:.14em;text-transform:uppercase;padding:20px 28px">{esc(item.get('cta') or 'More on our feed')}</div></div>
</div>"""
    return page(body, STORY_W, STORY_H, primary, fg, f".frame{{--line:{line};--muted:{fg}}}")


# ---------- render ----------

def render(date):
    from playwright.sync_api import sync_playwright

    q = json.loads((ROOT / "instagram" / "queue" / f"{date}.json").read_text())
    extra = ROOT / "instagram" / "extra" / f"{date}.json"
    if not q.get("evergreen") and extra.exists():
        q["evergreen"] = json.loads(extra.read_text())
    out = ROOT / "ig" / date
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("*.jpg")) + list(out.glob("*.mp4")):
        old.unlink()

    if q.get("feed", {}).get("kind") == "feature":
        img = feature_image(date)
        if img:
            q["feed"]["cover"]["image"] = img
            for s in q.get("stories", []):
                s.setdefault("image", img)
        else:
            print("Warning: today's feature has no photo in features.json - slide 1 will be plain black")
    jobs = [(f"feed-{i}.jpg", page(s, FEED_W, FEED_H, "#000000", "#FFFFFF", FEED_CSS), FEED_W, FEED_H)
            for i, s in enumerate(build_feed(q["feed"]), 1)]
    # Stories and Reels switched off (22 Oct 2026): carousels only.
    if RENDER_STORIES:
        jobs += [(f"story-{i}.jpg", story(s), STORY_W, STORY_H) for i, s in enumerate(q.get("stories", []), 1)]
    if q.get("evergreen"):
        jobs += [(f"evergreen-{i}.jpg", page(s, FEED_W, FEED_H, "#000000", "#FFFFFF", FEED_CSS), FEED_W, FEED_H)
                 for i, s in enumerate(build_evergreen(q["evergreen"]), 1)]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, doc, w, h in jobs:
            pg = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            pg.set_content(doc, wait_until="networkidle")
            pg.evaluate(FIT_JS)
            pg.screenshot(path=str(out / name), type="jpeg", quality=92, clip={"x": 0, "y": 0, "width": w, "height": h})
            pg.close()
        browser.close()

    feed_files = [j[0] for j in jobs if j[0].startswith("feed-")]
    reel = None
    if RENDER_REELS and q.get("reel", True) and feed_files:
        try:
            make_reel([out / f for f in feed_files], out / "reel.mp4")
            reel = "reel.mp4"
        except Exception as e:
            print("Reel render failed (carousel and stories unaffected):", e)
    prune()
    manifest = {
        "date": date,
        "feed": feed_files,
        "stories": [j[0] for j in jobs if j[0].startswith("story-")],
        "evergreen": [j[0] for j in jobs if j[0].startswith("evergreen-")],
        "reel": reel,
        "rendered_at": datetime.now(MEL).isoformat(timespec="seconds"),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"Rendered {len(jobs)} images to {out}")
    return manifest


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else datetime.now(MEL).date().isoformat())
