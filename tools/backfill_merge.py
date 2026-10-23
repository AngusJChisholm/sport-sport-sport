"""Merge researched backfill deals (TSV: date, brand, property, sport, type, summary, url) into deals.json.
Archive only: no "added" field (so they never join a day's edition), no articles. Skips repeats
(same brand and property in either order, matching names and aliases from entities.json)."""
import json, re, sys, glob, unicodedata
from pathlib import Path
root = Path(__file__).resolve().parent.parent
data = json.loads((root / "deals.json").read_text(encoding="utf-8"))
ents = json.loads((root / "entities.json").read_text(encoding="utf-8"))["entities"]
def n(s):
    s = unicodedata.normalize("NFKD", s); s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower().replace("&", " and ")).strip()
canon = {}
for slug, v in ents.items():
    for name in [v["name"], *v.get("aliases", [])]: canon[n(name)] = slug
RENAME = {"Melbourne City": "Melbourne City FC", "Manly Warringah Sea Eagles": "Manly Sea Eagles",
          "New Zealand Rugby League": "NZ Rugby League", "Hurricanes": "Hurricanes (Super Rugby)",
          "Blues": "Blues (Super Rugby)", "Tasmania Football Club": "Tasmania Devils"}
c = lambda s: canon.get(n(s), n(s))
def key(brand, prop): return frozenset([c(brand), c(prop)])
have = set()
for e in data["deals"]:
    sides = [x.strip() for x in e["deal"].split("×")]
    if len(sides) == 2:
        for b in sides[0].split(" / "):
            for p in sides[1].split(" / "): have.add(key(b.strip(), p.strip()))
added, skipped = [], []
for f in sorted(sys.argv[1:]):
    for line in open(f, encoding="utf-8"):
        if not line.strip(): continue
        cols = line.rstrip("\n").split("\t")
        date, brand, prop, sport, typ, summ, url = cols[:7]
        region = cols[7] if len(cols) > 7 else "ANZ"
        brand, prop = RENAME.get(brand, brand), RENAME.get(prop, prop)
        k = key(brand, prop)
        if k in have: skipped.append(f"{brand} × {prop}"); continue
        have.add(k)
        added.append({"date": date, "deal": f"{brand} × {prop}", "sport": sport, "type": typ,
                      "region": region, "summary": summ, "url": url})
data["deals"].extend(added)
# Appended, not re-sorted: the site sorts the archive itself, and the top of the list is the daily edition.
(root / "deals.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print("added", len(added), "skipped", len(skipped), "total", len(data["deals"]))
for x in skipped: print("  repeat:", x)
