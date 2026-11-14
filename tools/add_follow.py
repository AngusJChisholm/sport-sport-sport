"""Put the follow + Weekly Edition block at the bottom of every page, directly above the footer.

Safe to re-run: it removes any old copy (including the old mid-page one) and writes one fresh copy
as the last thing inside <main>. Edit the block here, then run:  python3 tools/add_follow.py
Then rebuild generated pages (python3 tools/build_articles.py, python3 tools/build_profiles.py).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LI = "https://www.linkedin.com/company/sportsportsport/"
IG = "https://www.instagram.com/sportsportsport.hq/"

BLOCK = f"""<!-- follow:start -->
<section class="sf" id="follow"><div class="sf-w">
<div class="sf-r"><div><h2>All things sport business.</h2><p>Partnerships, news and analysis on LinkedIn and Instagram.</p></div>
<div class="sf-a"><a class="sf-b" href="{LI}" target="_blank" rel="noopener">LinkedIn</a><a class="sf-b sf-o" href="{IG}" target="_blank" rel="noopener">Instagram</a></div></div>
<div class="sf-n" id="nl"><p><b>The Weekly Edition.</b> Every partnership from the week, in your inbox Monday mornings.</p><div class="nl-f" id="nlF"><span class="sf-b sf-soon" aria-disabled="true">Coming soon</span></div></div>
</div></section>
<!-- follow:end -->
"""

OLD_FO = re.compile(r'\n?<section class="dk fo"[^>]*>.*?</div></section>\n?', re.S)
MARKED = re.compile(r'\n?<!-- follow:start -->.*?<!-- follow:end -->\n?', re.S)


def apply(text, css_href):
    text = OLD_FO.sub("\n", text)
    text = MARKED.sub("\n", text)
    if "</main>" not in text:
        return None
    text = text.replace("</main>", BLOCK + "</main>", 1)
    text = re.sub(r"\n{3,}(<!-- follow:start -->)", r"\n\n\1", text)
    link = f'<link rel="stylesheet" href="{css_href}">'
    if "follow.css" not in text:
        text = text.replace("</head>", link + "\n</head>", 1)
    return text


def main():
    targets = [(p, "assets/follow.css") for p in sorted(ROOT.glob("*.html"))]
    targets.append((ROOT / "tools" / "article_template.html", "../assets/follow.css"))
    for p, href in targets:
        t = p.read_text(encoding="utf-8")
        new = apply(t, href)
        if new is None:
            print("skip (no <main>):", p.name)
            continue
        if new != t:
            p.write_text(new, encoding="utf-8")
            print("updated:", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
