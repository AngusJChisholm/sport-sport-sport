"""Adds structured fields to every deal in deals.json, from what the deal's own type and summary say.

  tier    what the partner gets: Naming rights, Title sponsor, Principal & major, Kit & apparel,
          Shirt & kit placement, Official partner, Media & broadcast, Licensing & merchandise,
          Ambassador & endorsement, Investment & ownership
  status  New, Renewal, Extension or Expansion
  term    length in years, only when the summary states it ("three-year deal")
  ends    the year the deal ends, only when the summary states it ("until 2029", "through 2027-28")
          or it can be worked out from a stated term and the announcement year (then endsEst is true)
  value   a reported deal value, word for word from the summary ("$5.3bn")

Nothing is guessed: a field is left out when the deal doesn't say. Fields already set by hand are never
overwritten, so a wrong one can be fixed in deals.json and stays fixed (set "tierLock": true to keep a tier).

Also fills "cat" (brand category) for new brand names in entities.json using the same keyword rules
the archive was first sorted with, and leaves anything unclear for a person to set.

Run: python3 tools/enrich.py   (safe to run any number of times)
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20}

TIER_BY_TYPE = [
    ("Naming rights", r"naming"),
    ("Title sponsor", r"title"),
    ("Principal & major", r"principal|major|premier|platinum|main sponsor|foundation|founding|front-of|premium partner|co-major"),
    ("Kit & apparel", r"kit supplier|apparel|footwear|training kit|outfitter|teamwear|uniform"),
    ("Shirt & kit placement", r"sleeve|back-of|shorts|jersey|shirt|patch|helmet|neckline|sternum"),
    ("Media & broadcast", r"media|broadcast|streaming|content|data rights"),
    ("Licensing & merchandise", r"licens|merch"),
    ("Ambassador & endorsement", r"ambassador|endorse|athlete"),
    ("Investment & ownership", r"investment|equity|ownership|acquisition|stake"),
    ("Official partner", r"partner|supplier|sponsor|supporter|associate|provider"),
]
# For renewals and plain "Partnership" deals the type says little, so read the summary too.
TIER_BY_TEXT = [
    ("Naming rights", r"\bnaming rights?\b|\btakes the name\b|\bbecomes [A-Z][\w&' ]+ (Stadium|Arena|Park|Oval)\b|\bnames? the (stadium|arena|venue|ground)\b"),
    ("Title sponsor", r"\btitle (sponsor|partner|rights|sponsorship)\b"),
    ("Principal & major", r"\b(principal|major|premier|platinum|main|front[- ]of[- ](shirt|jersey|guernsey))\b (partner|sponsor|deal|partnership)?"),
    ("Kit & apparel", r"\b(kit|apparel|teamwear|footwear) (supplier|partner|deal)\b|\bofficial outfitter\b"),
    ("Shirt & kit placement", r"\b(sleeve|back[- ]of[- ](shirt|shorts|jersey)|shorts|helmet|jersey patch)\b"),
    ("Media & broadcast", r"\b(broadcast|media rights|streaming rights|tv rights|free-to-air)\b"),
    ("Ambassador & endorsement", r"\b(ambassador|endorsement)\b"),
]


def tier_of(d):
    t = (d.get("type") or "").lower()
    s = d.get("summary") or ""
    if t in ("renewal", "extension", "expansion", "partnership", "partner", "sponsorship", "") or t.startswith("team partner"):
        for name, pat in TIER_BY_TEXT:
            if re.search(pat, s, re.I):
                return name
        return "Official partner"
    for name, pat in TIER_BY_TYPE:
        if re.search(pat, t):
            return name
    return "Official partner"


def status_of(d):
    if not d.get("date") and not d.get("month") and d.get("listed"):
        return "Current partner"   # taken from a club's partner page, announcement not found
    t = (d.get("type") or "").lower()
    s = (d.get("summary") or "").lower()
    if t == "renewal" or re.search(r"\b(renews?|renewed|re-signs?|re-signed|re-ups?|returns? (as|for)|continues?|stays|retained|reaffirms)\b", s):
        return "Renewal"
    if t == "extension" or re.search(r"\b(extends?|extended|extension)\b", s):
        return "Extension"
    if t == "expansion" or re.search(r"\b(expands?|expanded|upgrades?|upgraded|steps up|deepens)\b", s):
        return "Expansion"
    return "New"


NUM = r"(\d{1,2}|" + "|".join(WORDS) + r")"


TENURE_BEFORE = re.compile(r"(after|over|of|ended an?|ending an?|hitting|stretched to|out to|spanning|extending an?|extends an?|extending its|renews an?|its|now in its|longest|more than|almost|nearly)\s*$", re.I)
TENURE_AFTER = re.compile(r"^\s*(-long|long|relationship|history|association|of partnership|together|old)", re.I)


def term_of(text):
    # "extends its 22-year deal by seven years" -> 7: an explicit "by N years" wins.
    m = re.search(r"\bby (a further |another )?" + NUM + r" (more )?(years|seasons)\b", text, re.I)
    if m:
        n = m.group(2).lower()
        return WORDS.get(n) or int(n)
    # "three-year deal", "10-year agreement". Skips tenure ("after 20 years", "a 16-year relationship")
    # and season labels ("2026-27 season").
    for m in re.finditer(r"(?<![\d/–-])\b" + NUM + r"[- ](year|season)s?\b", text, re.I):
        if TENURE_BEFORE.search(text[max(0, m.start() - 22):m.start()]) or TENURE_AFTER.search(text[m.end():m.end() + 24]):
            continue
        n = m.group(1).lower()
        n = WORDS.get(n) or int(n)
        if 1 <= n <= 30:
            return n
    m = re.search(r"(?<!stood )(?<!been )\bfor (a further |another |)" + NUM + r" (more )?(years|seasons)\b", text, re.I)
    if m:
        n = m.group(2).lower()
        return WORDS.get(n) or int(n)
    return None


def ends_of(text):
    # "until 2029", "through 2027", "to the end of 2028", "through 2027-28", "until the end of the 2028 season"
    m = re.search(r"\b(until|till|through|thru|to|into|runs to|runs until|out to)( at least)?( the end of)?( the)? (20\d\d)(?:[-/–](\d\d|20\d\d))?\b", text, re.I)
    if m:
        y = int(m.group(5))
        if m.group(6):
            tail = m.group(6)
            y = int(tail) if len(tail) == 4 else int(str(y)[:2] + tail)
        if 2000 <= y <= 2060:
            return y
    # Season or year ranges: "covering 2026-2028", "for the 2026-27 season", "the 2028 to 2034 rights deal"
    ends = []
    for a, b in re.findall(r"\b(20\d\d)\s?(?:[-–/]|to)\s?(20\d\d|\d\d)\b", text):
        y = int(b) if len(b) == 4 else int(a[:2] + b)
        if int(a) < y <= int(a) + 25:
            ends.append(y)
    if ends:
        return max(ends)
    m = re.search(r"\bto (20\d\d)\b", text)
    if m:
        return int(m.group(1))
    return None


VAL = re.compile(r"((?:A|AU|US|NZ|C|HK)?[$£€₹]\s?\d[\d,.]*\s?(?:bn|billion|m|million|k|crore|cr)?\b|\b\d[\d,.]*\s?(?:billion|million|crore)\s(?:dollars|pounds|euros|rupees)?)", re.I)


def value_of(text):
    m = VAL.search(text)
    if not m:
        return None
    v = m.group(1).strip()
    # Only a value when the text says it's what the deal is worth, not a donation or prize pool
    near = text[max(0, m.start() - 60):m.end() + 40].lower()
    if not re.search(r"worth|reported|valued|deal|a year|per year|per season|investment|sponsorship|committing|over (five|three|four|two|\d+) years|buy|stake", near):
        return None
    if re.search(r"donat|prize|bracket|challenge|raise", near):
        return None
    # Ignore bare small numbers like "$5" with no unit
    if not re.search(r"bn|billion|m\b|million|k\b|crore|cr\b|\d{2,}[,.]?\d{3}", v, re.I):
        return None
    return v


def year_of(d):
    s = d.get("date") or d.get("month") or ""
    return int(s[:4]) if s[:4].isdigit() else None


def enrich_deal(d):
    # The summary is the source of truth. A lead article's standfirst is only read when the summary is silent,
    # and the article body (history and context) never is.
    summ = " ".join(x for x in [d.get("summary") or "", d.get("type") or ""] if x)
    art = d.get("article")
    stand = (art.get("standfirst") or "") if isinstance(art, dict) else ""
    if not d.get("tierLock"):
        d.setdefault("tier", tier_of(d))
    d.setdefault("status", status_of(d))
    if "term" not in d:
        t = term_of(summ) or (term_of(stand) if stand else None)
        if t:
            d["term"] = t
    if "ends" not in d:
        e = ends_of(summ) or (ends_of(stand) if stand else None)
        y = year_of(d)
        if e and y and y - 1 <= e <= y + 20:
            d["ends"] = e
        elif d.get("term") and y:
            d["ends"] = y + d["term"]
            d["endsEst"] = True
    if "value" not in d:
        v = value_of(d.get("summary") or "")
        if v:
            d["value"] = v
    return d


def tag_new_names(deals):
    """Gives brand names with no category a "cat", and property names a "ptype", where the rules are sure."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from category_rules import classify
    from build_profiles import norm, slugify, split, many
    ep = ROOT / "entities.json"
    E = json.loads(ep.read_text(encoding="utf-8"))
    ent = E["entities"]
    look = {}
    for slug, x in ent.items():
        look[norm(x["name"])] = slug
        for a in x.get("aliases", []):
            look[norm(a)] = slug
    clubs = {c for l in E.get("leagues", []) for c in l.get("clubs", [])}
    changed = 0
    for d in deals:
        b, p = split(d.get("deal"))
        for side, names in (("b", many(b)), ("p", many(p) if p else [])):
            for n in names:
                slug = look.get(norm(n)) or slugify(n)
                x = ent.get(slug)
                if x is None:
                    x = ent[slug] = {"name": n}
                    look[norm(n)] = slug
                    changed += 1
                if side == "b" and "cat" not in x:
                    c = classify(x["name"], x.get("domain", ""))
                    if c:
                        x["cat"] = c
                        changed += 1
                if side == "p" and "ptype" not in x and slug in clubs:
                    x["ptype"] = "Club & team"
                    changed += 1
    if changed:
        E["entities"] = dict(sorted(ent.items()))
        ep.write_text(json.dumps(E, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"entities.json: {changed} updates for new names")


def main():
    p = ROOT / "deals.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    before = json.dumps(data, ensure_ascii=False)
    for d in data["deals"]:
        enrich_deal(d)
    tag_new_names(data["deals"])
    after = json.dumps(data, ensure_ascii=False)
    if after != before:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("deals.json enriched")
    else:
        print("deals.json already up to date")


if __name__ == "__main__":
    main()
