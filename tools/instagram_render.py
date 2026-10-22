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

def feed_cover(c):
    ph = photo_layer(deal_image(c), FEED_W, SHADE_FEED) if (c.get("image") or c.get("deal")) else ""
    body = f"""<div class="frame{' photo' if ph else ''}">{ph}
<div class="top"><div class="tag">{esc(c.get('tag') or 'Deal of the day')}</div><div class="lbl" style="color:#9E9E9E">{esc(c.get('region',''))}</div></div>
<div style="display:flex;flex-direction:column;gap:40px">
<h1 class="disp" data-fit="640" style="font-size:196px">{highlight(c['headline'], c.get('highlight'))}</h1>
<div class="sup">{esc(c.get('deal',''))}{(' - ' + esc(c['descriptor'])) if c.get('descriptor') else ''}</div>
</div>
<div class="foot" style="border-top:1px solid #292929;padding-top:36px">{wordmark('white')}{SWIPE}</div>
</div>"""
    return body


def edge_bar(colour):
    """Club-colour edge. Pale colours (volt, yellows, white) get a black keyline so they hold up on white."""
    if not colour:
        return ""
    pale = " pale" if HEX.match(str(colour)) and luminance(colour) > 0.6 else ""
    return f'<div class="edge{pale}" style="background:{colour}"></div>'


def rows_slide(label, title, rows, n, total, footer_right="", edge=None):
    """Inner slide: club-colour edge, title, big numbered rows. (Only slide 1 carries the photo.)"""
    rows_html = "".join(
        f'<div class="nrow"><div class="n">{i:02d}</div><div><b>{esc(r.get("main"))}</b>'
        + (f'<span>{esc(r.get("sub"))}</span>' if r.get("sub") else "") + "</div></div>"
        for i, r in enumerate(rows, 1))
    title_html = f'<h2 class="disp title-xl" data-fit="270">{esc(title)}</h2>' if title else ""
    pad = "padding-top:56px"
    fit = 620
    if not title:
        fit += 260
    return f"""<div class="frame light">{edge_bar(edge)}
<div class="top"><div class="lbl">{esc(label)}</div>{counter(n, total)}</div>
<div class="mid" style="{pad};flex:1;justify-content:flex-start">
{title_html}
<div class="nrows" data-fit="{fit}" data-min="9">{rows_html}</div>
</div>
<div class="foot">{wordmark('black')}<div class="lbl mute" style="letter-spacing:.14em">{esc(footer_right)}</div></div>
</div>"""


def others_slide(others, n, total, edge=None):
    """Round-up slide: each deal with its sport, a short line and its own photo when it has one."""
    rows = []
    for o in others[:5]:
        sub = str(o.get("sub") or "")
        sport, _, rest = sub.partition(" - ")
        if not rest:
            sport, rest = "", sub
        th = ""
        rows.append(f'<div class="orow"><div>' + (f'<span class="s">{esc(sport)}</span>' if sport else "")
                    + f'<b>{esc(o["deal"])}</b>' + (f'<span class="x">{esc(rest)}</span>' if rest else "")
                    + f"</div>{th}</div>")
    return f"""<div class="frame light">{edge_bar(edge)}
<div class="top"><div class="lbl">Today's other deals</div>{counter(n, total)}</div>
<div class="mid" style="padding-top:36px;flex:1">
<div class="nrows" data-fit="1000" data-min="8" style="font-size:19px">{"".join(rows)}</div>
</div>
<div class="foot">{wordmark('black')}<div class="lbl mute" style="letter-spacing:.14em">{esc(SITE_LABEL)}</div></div>
</div>"""


def lead_edge(cover):
    """Club colour for the edge bar: the property's primary, or its secondary if the primary is near black."""
    cols = club_colours({"deal": cover.get("deal", ""), "colours": cover.get("colours")})
    for c in cols:
        if HEX.match(str(c)) and luminance(c) > 0.03:
            return c
    return VOLT


def feed_rows_slide(label, title, rows, n, total, footer_right=""):
    rows_html = "".join(
        f'<div class="row"><b>{esc(r.get("main"))}</b>' + (f'<span>{esc(r.get("sub"))}</span>' if r.get("sub") else "") + "</div>"
        for r in rows)
    title_html = f'<h2 class="disp" data-fit="330" style="font-size:120px">{esc(title)}</h2>' if title else ""
    return f"""<div class="frame light">
<div style="display:flex;flex-direction:column;gap:48px">
<div class="top"><div class="lbl">{esc(label)}</div>{counter(n, total)}</div>
{title_html}
<div class="rows" data-fit="{760 if title else 1000}" data-min="9">{rows_html}</div>
</div>
<div class="foot">{wordmark('black')}<div class="lbl mute" style="letter-spacing:.14em">{esc(footer_right)}</div></div>
</div>"""


def feed_close(n, total):
    return f"""<div class="frame light">
<div class="top"><div class="lbl">Sport Sport Sport</div>{counter(n, total)}</div>
<div style="display:flex;flex-direction:column;gap:40px">
<h2 class="disp" style="font-size:168px">All things <span class="v">sport</span> business.</h2>
<div class="sup">Global &amp; ANZ deals, every weekday</div>
</div>
<div class="foot">{wordmark('black')}<div style="background:{VOLT};color:#000;font-weight:800;font-size:26px;letter-spacing:.14em;text-transform:uppercase;padding:20px 28px">Follow for daily deals</div></div>
</div>"""


def week_item(item, idx, n, total, label="The week in deals"):
    ph = photo_layer(deal_image(item), FEED_W, SHADE_FEED)
    sub_col = "#E6E6E6" if ph else "#33332F"
    return f"""<div class="frame{' photo' if ph else ' light'}">{ph}
<div class="top"><div class="lbl">{esc(label)}</div>{counter(n, total)}</div>
<div style="display:flex;flex-direction:column;gap:36px">
<div class="disp v" style="font-size:220px">{idx:02d}</div>
<h2 class="disp" data-fit="420" style="font-size:132px">{esc(item['deal'])}</h2>
<div style="font-size:32px;line-height:1.4;color:{sub_col}">{esc(item.get('sub',''))}</div>
</div>
<div class="foot">{wordmark('white' if ph else 'black')}<div class="lbl mute">{esc(item.get('sport',''))}</div></div>
</div>"""


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
    slides = []
    if feed.get("kind") == "week":
        items = feed["items"][:8]
        total = len(items) + 2
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
    if q.get("reel", True) and feed_files:
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
