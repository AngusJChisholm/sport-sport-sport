"""Build one static article page per lead deal.

Reads deals.json, and for every deal with "lead": true and an "article" object,
writes articles/<slug>.html from tools/article_template.html. Run from the repo root:

    python3 tools/build_articles.py

A lead deal without a "slug" gets one generated from its date and deal name.
"""
import html
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://sportsportsport.netlify.app"


def make_slug(d, deal):
    s = unicodedata.normalize("NFKD", deal).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return f"{d}-{s}"[:80].rstrip("-")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def long_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.strftime('%A')} {d.day} {d.strftime('%B %Y')}"


def short_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day:02d} {d.strftime('%b')}"


def main():
    data = json.loads((ROOT / "deals.json").read_text(encoding="utf-8"))
    deals = data["deals"]
    linkedin = (data.get("site") or {}).get("linkedin", "")
    tpl = (ROOT / "tools" / "article_template.html").read_text(encoding="utf-8")
    out_dir = ROOT / "articles"
    out_dir.mkdir(exist_ok=True)

    changed_slugs = False
    built = []
    for e in deals:
        if not (e.get("lead") and e.get("article") and e.get("date")):
            continue
        if not e.get("slug"):
            e["slug"] = make_slug(e["date"], e["deal"])
            changed_slugs = True
        a = e["article"]
        tags = f'<span class="tag">{esc(e.get("sport"))}</span>'
        if e.get("type"):
            tags += f'<span class="tag">{esc(e["type"])}</span>'
        tags += f'<span class="tag r">{esc(e.get("region"))}</span>'
        body = "\n".join(f'<p class="b">{esc(p)}</p>' for p in a.get("body", []))
        source = ""
        if e.get("url"):
            source = f'<p class="src">Source: <a href="{esc(e["url"])}" target="_blank" rel="noopener">original announcement</a></p>'
        others = [o for o in deals if o.get("date") == e["date"] and o is not e]
        sameday = ""
        if others:
            rows = []
            for o in others:
                inner = f'<span><b>{esc(o["deal"])}</b><span class="x">{esc(o.get("sport"))} · {esc(o.get("summary") or o.get("type"))}</span></span><span>→</span>'
                if o.get("slug") and o.get("article"):
                    rows.append(f'<a class="row" href="{esc(o["slug"])}.html">{inner}</a>')
                elif o.get("url"):
                    rows.append(f'<a class="row" href="{esc(o["url"])}" target="_blank" rel="noopener">{inner}</a>')
                else:
                    rows.append(f'<div class="row">{inner[:-len("<span>→</span>")]}</div>')
            sameday = (
                '<section class="same"><div class="wrap"><span class="lbl mute-l" style="display:block;margin-bottom:16px">'
                f'Also on {esc(short_date(e["date"]))}</span><h2 class="disp">The other deals.</h2>'
                + "".join(rows)
                + "</div></section>"
            )
        follow = f'<a class="btn" href="{esc(linkedin)}" target="_blank" rel="noopener">Follow on LinkedIn</a>' if linkedin else ""
        title = e.get("headline") or e["deal"]
        page = (
            tpl.replace("{{TITLE}}", esc(f'{e["deal"]}: {title}'))
            .replace("{{DESC}}", esc(a.get("standfirst")))
            .replace("{{CANONICAL}}", f'{SITE_URL}/articles/{e["slug"]}.html')
            .replace("{{ISODATE}}", e["date"])
            .replace("{{LONGDATE}}", esc(long_date(e["date"])))
            .replace("{{HEADLINE}}", esc(title))
            .replace("{{DEAL}}", esc(e["deal"]))
            .replace("{{TAGS}}", tags)
            .replace("{{STANDFIRST}}", esc(a.get("standfirst")))
            .replace("{{BODY}}", body)
            .replace("{{CLOSE}}", esc(a.get("close")))
            .replace("{{SOURCE}}", source)
            .replace("{{SAMEDAY}}", sameday)
            .replace("{{FOLLOW}}", follow)
            .replace("{{YEAR}}", e["date"][:4])
        )
        (out_dir / f'{e["slug"]}.html').write_text(page, encoding="utf-8")
        built.append(e["slug"])

    if changed_slugs:
        (ROOT / "deals.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Built {len(built)} article pages")


if __name__ == "__main__":
    main()
