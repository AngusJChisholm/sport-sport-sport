"""Brand and property profiles for SSS Pro's Match Score (tools/match.py).

A match should make sense for who the brand sells to and what it stands for, not only where it already
sponsors. Every brand and property gets a profile:

  pos    positioning: "premium", "mid" or "value"
  mkt    market: "b2c", "b2b" or "both"            (brands only)
  aud    audience: who they reach (affluent, women, families, youth, men, business, active, fans, ...)
  align  what they stand for or show up around (luxury, fashion, hospitality, community, performance, ...)
  avoid  sports a brand stays away from (brands only, researched), e.g. Longines avoids contact team sports
  pnote, psrc  one line on the brand's sponsorship strategy and the source it came from (researched only)

Brands: researched values in entities.json ("pos", "mkt", "aud", "align", with "profiled": "YYYY-MM-DD")
win; otherwise the defaults below by sub-category, then by category. Researched profiles are marked so the
page can say which matches rest on research and which on defaults.

Properties: entities.json overrides win; otherwise the sport default, adjusted for property type (events add
hospitality and experiences), women's properties and global reach.
"""

# ---------------------------------------------------------------- brand defaults by sub-category
P, M, V = "premium", "mid", "value"
SUB = {
    # alcohol
    "Champagne & sparkling": (P, "b2c", ["affluent", "women", "adults"], ["luxury", "celebration", "fashion", "hospitality"]),
    "Spirits": (M, "b2c", ["adults", "affluent"], ["celebration", "hospitality", "lifestyle"]),
    "Wine": (M, "b2c", ["adults", "affluent", "women"], ["hospitality", "celebration", "lifestyle", "regional"]),
    "Beer & cider": (M, "b2c", ["men", "adults", "fans"], ["mateship", "fans", "hospitality", "summer"]),
    "Liquor retail": (V, "b2c", ["adults"], ["celebration", "convenience"]),
    # drinks
    "Energy drinks": (M, "b2c", ["youth", "men"], ["action", "performance", "music"]),
    "Sports & hydration": (M, "b2c", ["active", "youth"], ["performance", "health", "summer"]),
    "Water": (V, "b2c", ["families", "active"], ["health", "sustainability", "summer"]),
    "Coffee & tea": (M, "b2c", ["adults", "women"], ["lifestyle", "hospitality"]),
    "Dairy & milk": (V, "b2c", ["families", "youth"], ["health", "community", "family"]),
    "Soft drinks": (V, "b2c", ["youth", "families", "fans"], ["fans", "summer", "music"]),
    # food
    "Food delivery": (M, "b2c", ["youth", "families"], ["convenience", "fans", "digital"]),
    "Quick service food": (V, "b2c", ["families", "youth", "fans"], ["fans", "family", "community"]),
    "Snacks & confectionery": (V, "b2c", ["families", "youth"], ["family", "fans", "celebration"]),
    "Supplements & protein": (M, "b2c", ["active", "men"], ["performance", "health"]),
    "Packaged food": (V, "b2c", ["families"], ["family", "community", "health"]),
    # money
    "Payments & cards": (M, "b2c", ["affluent", "fans", "travellers"], ["experiences", "hospitality", "travel", "international"]),
    "Super & wealth": (M, "both", ["workers", "affluent", "business"], ["community", "future", "trust"]),
    "Banks": (M, "both", ["families", "business", "community"], ["community", "trust", "regional"]),
    "Health insurance": (M, "b2c", ["families", "active"], ["health", "wellness", "family"]),
    "Life insurance": (M, "b2c", ["families"], ["wellness", "family", "trust"]),
    "General insurance": (M, "b2c", ["families", "drivers"], ["community", "safety", "trust"]),
    "Crypto": (M, "b2c", ["youth", "men"], ["digital", "innovation", "international"]),
    "Trading & investing": (M, "b2c", ["men", "affluent"], ["innovation", "international"]),
    "Payments & BNPL": (M, "b2c", ["youth", "women"], ["digital", "lifestyle", "fashion"]),
    "Bookmakers": (M, "b2c", ["men", "punters", "fans"], ["wagering", "fans"]),
    "Prediction markets": (M, "b2c", ["men", "youth"], ["wagering", "digital"]),
    "Lotteries": (V, "b2c", ["adults", "families"], ["community", "wagering"]),
    # cars and travel
    "Car makers": (M, "b2c", ["families", "drivers", "men"], ["performance", "travel", "family"]),
    "Car dealers": (M, "b2c", ["drivers", "families", "local"], ["community", "local"]),
    "Motorcycles": (M, "b2c", ["men"], ["action", "performance"]),
    "Tyres": (M, "b2c", ["drivers", "men"], ["performance", "safety", "automotive"]),
    "Oils & parts": (M, "both", ["drivers", "men"], ["performance", "automotive"]),
    "Airlines": (M, "b2c", ["travellers", "affluent", "business"], ["travel", "international", "hospitality"]),
    "Hotels & resorts": (P, "b2c", ["travellers", "affluent"], ["hospitality", "travel", "luxury"]),
    "Travel booking": (M, "b2c", ["travellers", "families"], ["travel", "experiences"]),
    "Airports": (M, "b2c", ["travellers"], ["travel", "local"]),
    # tech and media
    "Social & content platforms": (M, "b2c", ["youth"], ["digital", "content", "culture", "music"]),
    "Wearables & health tech": (P, "b2c", ["active", "affluent"], ["health", "performance", "wellness", "innovation"]),
    "Consumer electronics": (M, "b2c", ["families", "men"], ["innovation", "entertainment", "fans"]),
    "IT services & consulting": (P, "b2b", ["business"], ["innovation", "data", "corporate hospitality"]),
    "Cybersecurity": (P, "b2b", ["business"], ["innovation", "trust", "corporate hospitality"]),
    "Sports data & tech": (M, "b2b", ["business", "fans"], ["data", "innovation"]),
    "Software & cloud": (M, "both", ["business"], ["innovation", "digital", "data"]),
    "AI": (P, "b2b", ["business"], ["innovation", "data"]),
    "Streaming & audio": (M, "b2c", ["youth", "fans"], ["content", "music", "culture"]),
    "Radio": (M, "b2c", ["commuters", "local", "fans"], ["content", "community", "music"]),
    "Publishing & news": (M, "b2c", ["adults", "women"], ["content", "fashion", "lifestyle"]),
    "Outdoor media": (M, "b2b", ["business"], ["content", "local"]),
    "Broadcast TV": (M, "b2c", ["fans", "families"], ["content", "fans"]),
    # hospitality and retail
    "Ticketing": (M, "b2c", ["fans"], ["events", "experiences", "music"]),
    "Casinos & hotels": (P, "b2c", ["affluent", "adults"], ["hospitality", "entertainment", "luxury", "celebration"]),
    "Attractions & venues": (M, "b2c", ["families", "youth"], ["experiences", "family", "entertainment"]),
    "Cinemas": (V, "b2c", ["families", "youth"], ["entertainment", "family"]),
    "Pubs, bars & restaurants": (M, "b2c", ["adults", "fans"], ["hospitality", "fans", "mateship"]),
    "Live events & music": (M, "b2c", ["youth", "adults"], ["music", "experiences", "culture"]),
    "Supermarkets": (V, "b2c", ["families"], ["family", "community", "health"]),
    "Hardware & home": (V, "b2c", ["families", "men", "local"], ["community", "home", "family"]),
    "Electronics retail": (V, "b2c", ["families", "men"], ["entertainment", "fans"]),
    "Sports retail": (M, "b2c", ["active", "youth", "fans"], ["performance", "fans"]),
    "Department & fashion retail": (M, "b2c", ["women", "families"], ["fashion", "lifestyle"]),
    "Pharmacy retail": (V, "b2c", ["families", "women"], ["health", "community"]),
    "Pharmacy & medical": (M, "both", ["families", "active"], ["health", "community"]),
    "Fitness clubs": (M, "b2c", ["active", "youth"], ["health", "wellness", "performance"]),
    "Vitamins & wellness": (M, "b2c", ["women", "active"], ["health", "wellness"]),
    "Beauty & personal care": (M, "b2c", ["women", "youth"], ["beauty", "fashion", "wellness"]),
    # apparel and luxury
    "Kit supplier": (M, "b2c", ["active", "fans", "youth"], ["performance", "fans"]),
    "Fashion & lifestyle": (P, "b2c", ["affluent", "women", "men"], ["fashion", "lifestyle", "luxury"]),
    "Activewear & recovery": (M, "b2c", ["active", "women"], ["wellness", "performance", "lifestyle"]),
    "Headwear & licensing": (M, "b2c", ["fans", "youth"], ["fans", "culture"]),
    "Watches": (P, "b2c", ["affluent", "men"], ["luxury", "precision", "tradition", "prestige"]),
    "Jewellery": (P, "b2c", ["affluent", "women"], ["luxury", "fashion", "celebration"]),
    "Fashion houses": (P, "b2c", ["affluent", "women"], ["luxury", "fashion", "prestige"]),
    # other
    "Fuel & oil": (V, "b2c", ["drivers"], ["travel", "convenience"]),
    "Renewables & solar": (M, "both", ["families", "business"], ["sustainability", "innovation"]),
    "Energy retail": (M, "b2c", ["families"], ["community", "sustainability", "home"]),
    "Telco": (M, "b2c", ["families", "youth"], ["connectivity", "digital", "fans"]),
    "Balls & racquets": (M, "b2c", ["active"], ["performance"]),
    "Golf": (P, "b2c", ["affluent", "men"], ["performance", "precision"]),
    "Bikes & cycling": (M, "b2c", ["active"], ["performance", "sustainability"]),
    "Drinkware & outdoor": (M, "b2c", ["active", "youth"], ["lifestyle", "sustainability"]),
}
CAT = {
    "Construction & property": (M, "both", ["families", "business", "local"], ["community", "local", "home"]),
    "Education": (M, "b2c", ["youth", "families"], ["community", "future"]),
    "Tourism & government": (M, "b2c", ["visitors", "families"], ["tourism", "community", "national pride"]),
    "Logistics & transport": (M, "b2b", ["business"], ["reliability", "corporate hospitality"]),
    "Professional services": (P, "b2b", ["business"], ["corporate hospitality", "community"]),
    "Agriculture": (M, "b2b", ["regional"], ["community", "regional"]),
    "Mining & resources": (M, "b2b", ["regional", "workers"], ["community", "regional", "future"]),
    "Industrial & manufacturing": (M, "b2b", ["business"], ["reliability", "local"]),
    "Not-for-profit": (V, "b2c", ["community"], ["community", "health"]),
    "Gaming & esports": (M, "b2c", ["youth", "men"], ["digital", "culture", "entertainment"]),
    "Collectibles & licensing": (M, "b2c", ["fans", "youth"], ["fans", "culture"]),
    "Home & hardware": (M, "b2c", ["families"], ["home", "innovation"]),
    "Retail": (V, "b2c", ["families"], ["community"]),
    "Health & beauty": (M, "b2c", ["women", "families"], ["health", "wellness"]),
    "Technology": (M, "both", ["business", "youth"], ["innovation", "digital"]),
    "Media & broadcast": (M, "b2c", ["fans"], ["content"]),
    "Hospitality & entertainment": (M, "b2c", ["adults", "families"], ["hospitality", "entertainment"]),
    "Automotive": (M, "b2c", ["drivers", "men"], ["automotive", "performance"]),
    "Airlines & travel": (M, "b2c", ["travellers"], ["travel"]),
    "Alcohol": (M, "b2c", ["adults"], ["hospitality", "celebration"]),
    "Non-alcoholic drinks": (V, "b2c", ["families", "youth"], ["refreshment", "fans"]),
    "Food & nutrition": (V, "b2c", ["families"], ["family", "fans"]),
    "Banking & finance": (M, "both", ["families", "business"], ["trust", "community"]),
    "Insurance": (M, "b2c", ["families"], ["trust", "safety"]),
    "Apparel & footwear": (M, "b2c", ["active", "youth"], ["performance", "lifestyle"]),
    "Sporting goods & equipment": (M, "b2c", ["active"], ["performance"]),
    "Watches & luxury": (P, "b2c", ["affluent"], ["luxury", "prestige"]),
    "Energy & utilities": (M, "b2c", ["families"], ["community", "sustainability"]),
    "Telco": (M, "b2c", ["families", "youth"], ["connectivity", "digital"]),
    "Betting & wagering": (M, "b2c", ["men", "punters"], ["wagering", "fans"]),
    "Fintech, crypto & trading": (M, "b2c", ["youth", "men"], ["digital", "innovation"]),
    "Sport & events": (M, "b2c", ["fans"], ["fans", "events"]),
}
# Premium names inside mass sub-categories (positioning follows the brand, not the slot).
PREMIUM_NAMES = ["lexus", "mercedes", "bmw", "audi", "porsche", "range rover", "land rover", "jaguar", "genesis", "volvo",
                 "polestar", "maserati", "aston martin", "bentley", "rolls-royce", "ferrari", "american express", "amex",
                 "qantas", "emirates", "qatar airways", "singapore airlines", "etihad", "crown", "penfolds", "grey goose",
                 "hennessy", "johnnie walker", "don julio", "mumm", "moet", "veuve", "laurent-perrier", "nespresso",
                 "lavazza", "r.m.williams", "ralph lauren", "lacoste", "boss", "hugo", "country road", "myer", "david jones",
                 "macquarie", "ubs", "howden", "accor", "marriott", "hyatt", "hilton", "four seasons", "sofitel"]
VALUE_NAMES = ["aldi", "kmart", "big w", "jetstar", "budget", "rebel", "supercheap", "red rooster", "hungry jack"]

# ---------------------------------------------------------------- property defaults by sport
SPORT = {
    "Horse racing": (P, ["affluent", "women", "adults", "punters"], ["fashion", "luxury", "hospitality", "celebration", "wagering", "tradition", "equestrian", "elegance"]),
    "Tennis": (P, ["affluent", "women", "families", "international"], ["luxury", "fashion", "wellness", "hospitality", "international", "innovation", "summer"]),
    "Golf": (P, ["affluent", "men", "business"], ["luxury", "precision", "corporate hospitality", "travel", "tradition"]),
    "AFL": (M, ["families", "men", "fans", "community"], ["fans", "community", "mateship", "family"]),
    "AFLW": (M, ["women", "families", "youth"], ["community", "equality", "family"]),
    "NRL": (M, ["men", "families", "fans"], ["fans", "mateship", "community"]),
    "NRLW": (M, ["women", "families"], ["community", "equality"]),
    "Cricket": (M, ["families", "men", "fans"], ["summer", "fans", "tradition", "community", "family"]),
    "Football": (M, ["youth", "families", "multicultural", "fans"], ["fans", "community", "international", "culture"]),
    "Basketball": (M, ["youth", "multicultural", "fans"], ["culture", "music", "digital", "action"]),
    "Netball": (M, ["women", "families", "youth"], ["community", "wellness", "equality", "family"]),
    "Motorsport": (M, ["men", "drivers", "fans"], ["performance", "automotive", "innovation", "action"]),
    "Rugby union": (M, ["affluent", "men", "business"], ["tradition", "corporate hospitality", "international"]),
    "Surfing": (M, ["youth", "active"], ["lifestyle", "action", "sustainability", "summer"]),
    "Cycling": (M, ["active", "affluent"], ["performance", "wellness", "sustainability", "travel"]),
    "Athletics": (M, ["active", "families"], ["performance", "wellness", "national pride"]),
    "Olympics": (M, ["families", "active"], ["national pride", "performance", "wellness"]),
    "Multi-sport": (M, ["families", "active"], ["national pride", "community", "wellness"]),
    "Esports": (M, ["youth", "men"], ["digital", "culture", "gaming"]),
    "Sailing": (P, ["affluent"], ["luxury", "sustainability", "innovation", "travel"]),
    "Hockey": (M, ["families", "active"], ["community", "performance"]),
    "Swimming": (M, ["families", "active"], ["wellness", "summer", "national pride"]),
}
DEFAULT_SPORT = (M, ["fans", "families"], ["fans", "community"])


def brand_profile(slug, ent, sub, cat):
    e = ent.get(slug) or {}
    base = SUB.get(sub) or CAT.get(cat) or (M, "b2c", [], [])
    pos, mkt, aud, align = base
    name = (e.get("name") or slug).lower()
    if any(n in name for n in PREMIUM_NAMES):
        pos = P
    elif any(n in name for n in VALUE_NAMES):
        pos = V
    researched = bool(e.get("profiled"))
    return {"pos": e.get("pos") or pos, "mkt": e.get("mkt") or mkt, "aud": e.get("aud") or list(aud),
            "align": e.get("align") or list(align), "avoid": e.get("avoid") or [], "avoid_class": e.get("avoid_class") or [], "note": e.get("pnote") or "",
            "researched": researched}


def property_profile(slug, ent, sport, pclass, reach, name):
    e = ent.get(slug) or {}
    pos, aud, align = SPORT.get(sport, DEFAULT_SPORT)
    aud, align = list(aud), list(align)
    n = (name or "").lower()
    if "women" in n or n.endswith("w") and sport in ("AFL", "NRL") or "aflw" in n or "wbbl" in n or "wnbl" in n or "matildas" in n or "wallaroos" in n:
        aud = ["women"] + [a for a in aud if a != "men"]
        align = align + ["equality"]
    if pclass == "event":
        align = align + ["hospitality", "experiences"]
    if reach == "Global":
        aud = aud + ["international"]
        align = align + ["international"]
    return {"pos": e.get("pos") or pos, "aud": e.get("aud") or sorted(set(aud)), "align": e.get("align") or sorted(set(align)),
            "sport": sport, "researched": bool(e.get("profiled"))}


def alignment(bp, pp):
    """0-1: how well a brand's profile fits a property's. Audience and values overlap, plus positioning."""
    a = set(bp["aud"]) & set(pp["aud"])
    v = set(bp["align"]) & set(pp["align"])
    s = min(1, len(a) / 2) * 0.4 + min(1, len(v) / 2) * 0.45
    if pp.get("sport") in bp.get("avoid", []):
        return 0.0, []  # the brand has said it stays away from this sport
    if bp["pos"] == pp["pos"]:
        s += 0.15
    elif {bp["pos"], pp["pos"]} == {P, V}:
        s -= 0.2  # a value brand at a premium property (or the reverse) rarely lands
    return max(0.0, min(1.0, s)), sorted(a | v)
