#!/usr/bin/env python3
"""SSS Pro coverage helper.

  python3 tools/coverage.py next 12   -> the next properties to check (never checked first, lowest tier first, then oldest)
  python3 tools/coverage.py stats     -> ANZ deal count vs target, properties checked, stale checks
  python3 tools/coverage.py show "Brisbane Lions"  -> every deals.json entry for that property (current partners first)
"""
import json, sys, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
cov = json.loads((ROOT / "coverage.json").read_text())
deals = json.loads((ROOT / "deals.json").read_text())["deals"]


def prop(d):
    return d["deal"].split(" × ", 1)[-1].strip()


def key(p):
    return (p["lastChecked"] is not None, p["lastChecked"] or "", p["tier"])


cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

if cmd == "next":
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    for p in sorted(cov["properties"], key=key)[:n]:
        have = sum(1 for d in deals if prop(d) == p["name"])
        print(f'{p["name"]} | {p["sport"]} | {p["state"]} | tier {p["tier"]} | last {p["lastChecked"]} | url {p["partnersUrl"]} | in archive {have}')

elif cmd == "show":
    name = sys.argv[2]
    rows = [d for d in deals if prop(d) == name]
    rows.sort(key=lambda d: (not d.get("listed"), d.get("date") or d.get("month") or ""))
    for d in rows:
        when = d.get("date") or d.get("month") or ("listed " + d.get("listed", ""))
        print(f'{d["deal"]} | {d.get("type")} | {when} | {d.get("url", "")}')
    print(len(rows), "entries")

else:
    anz = [d for d in deals if d.get("region") == "ANZ"]
    ps = cov["properties"]
    checked = [p for p in ps if p["lastChecked"]]
    cutoff = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
    stale = [p for p in checked if p["lastChecked"] < cutoff]
    print(f'ANZ deals: {len(anz)} of {cov["target"]} target ({len(anz) * 100 // cov["target"]}%)')
    print(f'Current partners from official pages: {sum(1 for d in anz if d.get("listed"))}')
    print(f'Properties checked: {len(checked)} of {len(ps)}; due a re-check (90+ days): {len(stale)}')
    for t in sorted({p["tier"] for p in ps}):
        tp = [p for p in ps if p["tier"] == t]
        print(f'  tier {t}: {sum(1 for p in tp if p["lastChecked"])}/{len(tp)} checked')
