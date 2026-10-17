"""Copy every Unsplash photo used in deals.json and features.json onto the site (assets/img/u/<photo-id>.jpg),
so photos load even where images.unsplash.com is blocked (e.g. work networks). Runs on GitHub.

    python3 tools/fetch_photos.py
"""
import json, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "u"
OUT.mkdir(parents=True, exist_ok=True)
got = 0
items = json.loads((ROOT / "deals.json").read_text())["deals"]
if (ROOT / "features.json").exists():
    items += json.loads((ROOT / "features.json").read_text()).get("features", [])
for d in items:
    m = re.match(r"^https://images\.unsplash\.com/(photo-[\w-]+)", str(d.get("image") or ""))
    if not m:
        continue
    dest = OUT / f"{m.group(1)}.jpg"
    if dest.exists() and dest.stat().st_size > 10_000:
        continue
    url = f"https://images.unsplash.com/{m.group(1)}?w=1600&q=80&fm=jpg&fit=crop"
    req = urllib.request.Request(url, headers={"User-Agent": "SportSportSport/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            dest.write_bytes(r.read())
        got += 1
        print("saved", dest.name)
    except Exception as e:
        print("failed", m.group(1), e)
print(f"{got} new photo(s)")
