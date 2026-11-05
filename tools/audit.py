"""Data audit for the SSS archive: finds likely errors so the data (and SSS Pro's matches) stay accurate.

    python3 tools/audit.py          # print the summary, write pro/audit.json
    python3 tools/audit.py --full   # also print every item

Checks (ANZ first, then everything):
  dup_entities    two organisations that are probably the same (Crown / Crown Resorts) -> merge with "aliases"
  no_category     brands with deals but no "cat"
  cat_mismatch    a brand's "cat" disagrees with the keyword rules (tools/category_rules.py) -> check by hand
  slot_clash      a property with two live partners in the same exclusive slot (two banks, two kit suppliers):
                  usually a partner that has left and needs "ended", or a wrong tag
  dup_deals       the same brand and property twice with the same date, or a "listed" entry next to a dated one
  no_broadcaster  ANZ leagues and governing bodies with no live broadcast partner
  stale           dated deals 4+ years old with no end year and no "ended": probably over
  no_source       deals with no url, or still flagged needsSource
"""
import json, re, sys, collections, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import match as M
from category_rules import classify as catrule

# Slots where a property almost always has only one partner at a time.
EXCLUSIVE = {"Banks", "Car makers", "Telco", "Airlines", "Energy retail", "Beer & cider", "Performance & kit",
             "Health insurance", "Supermarkets", "Quick service food", "Payments & cards", "Fuel & oil",
             "Ticketing", "Energy drinks", "Sports & hydration", "Tyres", "Watches"}
SUFFIX = re.compile(r"\b(group|resorts|sports|sport|ltd|limited|pty|inc|holdings|the|official|international|global)\b")
COUNTRY = re.compile(r"\b(australia|aus|au|nz|new zealand|aotearoa)\b")


def base(n):
    """Name without company suffixes. A country word is only dropped from the end ("LEGO Australia" = "LEGO"),
    so "Cricket Australia" and "New Zealand Cricket" stay apart."""
    n = SUFFIX.sub(" ", M.norm(n))
    n = re.sub(r"\s+(australia|aus|au|nz|new zealand)$", "", re.sub(r"\s+", " ", n).strip())
    return n if not COUNTRY.search(n) else n + "#c"


def main():
    ent, deals, league_of = M.load()
    today = datetime.date.today()
    now = today.year * 12 + today.month - 1
    m = M.Model(ent, deals, league_of, now)
    nm = lambda s: ent.get(s, {}).get("name") or m.name.get(s, s)
    anz = lambda p: m.region.get(p) == "ANZ"
    out = collections.OrderedDict()

    # duplicates: same base name, both used in deals
    used = set(m.B) | set(m.P)
    groups = collections.defaultdict(set)
    for s in used:
        b = base(nm(s))
        if len(b) >= 3:
            groups[b].add(s)
    out["dup_entities"] = [{"names": sorted(nm(s) for s in g), "slugs": sorted(g)} for b, g in groups.items() if len(g) > 1]

    out["no_category"] = sorted(({"brand": nm(b), "slug": b, "deals": len(rs)} for b, rs in m.B.items() if not m.cat.get(b)),
                                key=lambda x: -x["deals"])
    mism = []
    for b, rs in m.B.items():
        c = m.cat.get(b)
        r = catrule(nm(b), (ent.get(b) or {}).get("domain", ""))
        if c and r and r != c:
            mism.append({"brand": nm(b), "slug": b, "cat": c, "rules_say": r, "deals": len(rs)})
    out["cat_mismatch"] = sorted(mism, key=lambda x: -x["deals"])

    clash = []
    for p, rs in m.P.items():
        by = collections.defaultdict(dict)
        for r in rs:
            sub = m.sub.get(r["b"])
            if r["live"] and sub in EXCLUSIVE:
                prev = by[sub].get(r["b"])
                if not prev or r["ym"] > prev["ym"]:
                    by[sub][r["b"]] = r
        for sub, bs in by.items():
            if len(bs) > 1:
                clash.append({"property": nm(p), "anz": anz(p), "slot": sub,
                              "partners": [{"brand": nm(b), "since": M.fmt_ym(r["ym"]) if r["dated"] else "listed",
                                            "ends": r["d"].get("ends")} for b, r in sorted(bs.items(), key=lambda x: -x[1]["ym"])]})
    out["slot_clash"] = sorted(clash, key=lambda x: (not x["anz"], x["property"]))

    dd, seen = [], collections.defaultdict(list)
    for x in deals:
        for b in x["bs"]:
            for p in x["ps"]:
                seen[(b, p)].append(x["d"])
    for (b, p), ds in seen.items():
        dates = [d.get("date") or d.get("month") for d in ds if d.get("date") or d.get("month")]
        if len(dates) != len(set(dates)):
            dd.append({"deal": f"{nm(b)} × {nm(p)}", "issue": "same date twice"})
        if dates and any(d.get("listed") and not (d.get("date") or d.get("month")) for d in ds):
            dd.append({"deal": f"{nm(b)} × {nm(p)}", "issue": "listed entry next to a dated one (drop the listed one)"})
    out["dup_deals"] = dd

    nb = []
    for p in m.P:
        if m.pclass[p] == "body" and anz(p) and len(m.P[p]) >= 5:
            if not any(r["live"] and m.cat.get(r["b"]) == "Media & broadcast" and r["d"].get("tier") in ("Media & broadcast", None)
                       or (r["live"] and m.sub.get(r["b"]) in ("Broadcast TV", "Streaming & audio")) for r in m.P[p]):
                nb.append({"property": nm(p), "deals": len(m.P[p])})
    out["no_broadcaster"] = sorted(nb, key=lambda x: -x["deals"])

    out["stale"] = [{"deal": x["d"]["deal"], "date": x["d"].get("date") or x["d"].get("month")}
                    for x in deals if x["ym"] is not None and now - x["ym"] >= 48 and not x["d"].get("ends") and not x["d"].get("ended")]
    out["no_source"] = [{"deal": x["d"]["deal"], "issue": "needsSource" if x["d"].get("needsSource") else "no url"}
                        for x in deals if x["d"].get("needsSource") or not x["d"].get("url")]

    summary = {k: len(v) for k, v in out.items()}
    summary["anz_slot_clash"] = sum(1 for c in out["slot_clash"] if c["anz"])
    res = {"generated": today.isoformat(), "summary": summary, **out}
    (ROOT / "pro").mkdir(exist_ok=True)
    (ROOT / "pro" / "audit.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Audit", summary)
    if "--full" in sys.argv:
        for k, v in out.items():
            print(f"\n== {k} ({len(v)})")
            for i in v[:400]:
                print("  ", json.dumps(i, ensure_ascii=False))


if __name__ == "__main__":
    main()
