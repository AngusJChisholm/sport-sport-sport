"""Property tiers: each property's own partner groupings, as its official partners page shows them.

Two layers on every deal:
  "tier"  - SSS's own deal type (Principal & major, Official partner ...). Same meaning everywhere; used for
            filters, insights, renewals and SSS Pro.
  "ptier" - the property's own grouping for that partner, exactly as its official partners page labels it
            (e.g. "Platinum partner", "Premier partner", "Official supplier"). Shown on the property's page.
  "ptitle"- optional: the partner's official title on that page (e.g. "Official Airline Partner").

On the property in entities.json:
  "ptiers"  - that property's groupings in the order its partners page shows them (top tier first).
  "ptiersChecked" - YYYY-MM-DD the order was last checked against the official page.

Run after deals.json changes (safe to re-run):  python3 tools/ptiers.py
 - A "listed" deal (taken from the official partners page) without a ptier gets its "type" as its ptier.
 - Any other deal for the same brand and property inherits that ptier (so a news "Extension" still sits in
   the right group on the property page).
 - Each property's "ptiers" is filled in where missing, and extended with any new grouping. An order that's
   been checked against the page ("ptiersChecked") is never reshuffled; new groupings are added at the end.
Small or flat partners pages with no groupings: leave ptier off. The page shows one "Partners" group.
"""
import json, re
from pathlib import Path
from build_profiles import norm, slugify, split, many

ROOT = Path(__file__).resolve().parent.parent

# Default top-to-bottom order for common groupings, used only until the order is checked on the page.
RANK = [r"naming rights|title", r"principal|founding|foundation major|co-major|^major|major partner", r"diamond|icon|elite",
        r"platinum", r"premier|premium|executive", r"gold", r"silver", r"bronze", r"associate|corporate|business|club partner",
        r"official partner|^partner$|category", r"apparel|kit|guernsey|jersey", r"media|broadcast|advertising",
        r"official supplier|supply|supplier|supporting|event supporter", r"university|education|medical|health|stadium|host|ticketing|member",
        r"community|charity|foundation|diversity|sustainability|pathways|government"]


def rank(label):
    l = label.lower()
    for i, r in enumerate(RANK):
        if re.search(r, l):
            return i
    return len(RANK)


def main():
    E = json.loads((ROOT / "entities.json").read_text(encoding="utf-8"))
    ent = E["entities"]
    look = {}
    for s, x in ent.items():
        look[norm(x["name"])] = s
        for a in x.get("aliases", []):
            look[norm(a)] = s
    res = lambda n: look.get(norm(n)) or slugify(n)
    DJ = json.loads((ROOT / "deals.json").read_text(encoding="utf-8"))
    deals = DJ["deals"]

    def pair(d):
        b, p = split(d.get("deal"))
        return ([res(x) for x in many(b)], [res(x) for x in many(p)] if p else [])

    set_listed = set_inherit = 0
    known = {}  # (brand, property) -> ptier from the official page
    for d in deals:
        if d.get("listed") and not d.get("ptier") and d.get("type"):
            d["ptier"] = d["type"]
            set_listed += 1
        if d.get("ptier"):
            bs, ps = pair(d)
            for b in bs:
                for p in ps:
                    known.setdefault((b, p), d["ptier"])
    for d in deals:
        if d.get("ptier") or d.get("ended"):
            continue
        bs, ps = pair(d)
        hit = next((known[(b, p)] for b in bs for p in ps if (b, p) in known), None)
        if hit:
            d["ptier"] = hit
            set_inherit += 1

    # Order of groupings per property: first appearance on the page (listed order), then default rank.
    seen = {}
    for d in deals:
        if d.get("ptier"):
            for p in pair(d)[1]:
                o = seen.setdefault(p, [])
                if d["ptier"] not in o:
                    o.append(d["ptier"])
    ent_new = ent_upd = 0
    for p, labels in seen.items():
        if p not in ent:
            continue
        e = ent[p]
        cur = e.get("ptiers") or []
        if not cur:
            e["ptiers"] = sorted(labels, key=lambda l: (rank(l), labels.index(l)))
            ent_new += 1
        else:
            add = [l for l in labels if l not in cur]
            if add:
                e["ptiers"] = cur + sorted(add, key=rank) if e.get("ptiersChecked") else sorted(cur + add, key=lambda l: (rank(l), (cur + add).index(l)))
                ent_upd += 1

    (ROOT / "deals.json").write_text(json.dumps(DJ, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "entities.json").write_text(json.dumps(E, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ptier: {set_listed} from official pages, {set_inherit} inherited; ptiers: {ent_new} properties set, {ent_upd} extended")


if __name__ == "__main__":
    main()
