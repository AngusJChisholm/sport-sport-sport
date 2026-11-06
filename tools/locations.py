"""Home city for ANZ clubs, used by SSS Pro's Match Score (tools/match.py).

Clubs look at other clubs in the same city across every code: a brand backing Melbourne Storm or Melbourne
Victory is a real prospect for Collingwood. Tasmanian teams are grouped as "Tasmania" (state-wide fan bases).
Set "city" on a property in entities.json to override or add one.
"""
CITY = {
    # Melbourne
    **{s: "Melbourne" for s in [
        "melbourne", "collingwood", "carlton", "essendon", "richmond", "hawthorn", "north-melbourne", "st-kilda",
        "western-bulldogs", "melbourne-storm", "melbourne-victory", "melbourne-city-fc", "melbourne-united",
        "south-east-melbourne-phoenix", "melbourne-vixens", "melbourne-mavericks", "melbourne-renegades",
        "melbourne-stars", "victoria-racing-club", "melbourne-racing-club", "melbourne-rebels", "melbourne-boomers",
        "western-united", "moonee-valley-racing-club"]},
    "geelong-cats": "Geelong", "geelong-united": "Geelong", "bendigo-spirit": "Bendigo",
    # Sydney
    **{s: "Sydney" for s in [
        "sydney-swans", "gws-giants", "sydney-roosters", "south-sydney-rabbitohs", "wests-tigers",
        "canterbury-bankstown-bulldogs", "parramatta-eels", "penrith-panthers", "cronulla-sharks", "manly-sea-eagles",
        "st-george-illawarra-dragons", "sydney-fc", "western-sydney-wanderers", "sydney-kings", "nsw-swifts",
        "giants-netball", "sydney-sixers", "sydney-thunder", "nsw-waratahs", "australian-turf-club", "sydney-flames",
        "macarthur-fc"]},
    "newcastle-knights": "Newcastle", "newcastle-jets": "Newcastle", "illawarra-hawks": "Wollongong",
    "central-coast-mariners": "Central Coast",
    # Queensland
    **{s: "Brisbane" for s in [
        "brisbane-lions", "brisbane-broncos", "dolphins", "brisbane-roar", "brisbane-bullets", "brisbane-heat",
        "queensland-reds", "queensland-firebirds", "brisbane-racing-club", "queensland-cricket"]},
    "gold-coast-suns": "Gold Coast", "gold-coast-titans": "Gold Coast", "gold-coast-turf-club": "Gold Coast",
    "sunshine-coast-lightning": "Sunshine Coast", "north-queensland-cowboys": "Townsville",
    "townsville-fire": "Townsville", "cairns-taipans": "Cairns",
    # Adelaide, Perth, Canberra, Tasmania
    **{s: "Adelaide" for s in [
        "adelaide-crows", "port-adelaide", "adelaide-united", "adelaide-36ers", "adelaide-thunderbirds",
        "adelaide-strikers", "adelaide-lightning"]},
    **{s: "Perth" for s in [
        "west-coast-eagles", "fremantle", "perth-wildcats", "perth-glory", "west-coast-fever", "perth-scorchers",
        "perth-bears", "western-force", "perth-lynx"]},
    **{s: "Canberra" for s in ["canberra-raiders", "act-brumbies", "uc-capitals", "canberra-united"]},
    **{s: "Tasmania" for s in ["tasmania-devils", "tasmania-jackjumpers", "hobart-hurricanes", "tasmania-jewels"]},
    # New Zealand and the Pacific
    **{s: "Auckland" for s in ["nz-warriors", "auckland-fc", "nz-breakers", "blues"]},
    **{s: "Wellington" for s in ["wellington-phoenix", "hurricanes", "hurricanes-poua"]},
    "crusaders": "Christchurch", "matat": "Christchurch", "chiefs": "Hamilton",
    "png-chiefs": "Port Moresby", "fijian-drua": "Fiji",
}


# Market (state, or country outside Australia) for a property, so a brand that only sells in some states isn't
# pointed at a property outside them (EnergyAustralia doesn't retail in WA, Tasmania, the NT or NZ).
# North and far-north Queensland is "QLD-REG": several energy retailers only sell in south-east Queensland.
CITY_STATE = {
    "Melbourne": "VIC", "Geelong": "VIC", "Bendigo": "VIC", "Ballarat": "VIC",
    "Sydney": "NSW", "Newcastle": "NSW", "Wollongong": "NSW", "Central Coast": "NSW",
    "Brisbane": "QLD", "Gold Coast": "QLD", "Sunshine Coast": "QLD", "Townsville": "QLD-REG", "Cairns": "QLD-REG",
    "Adelaide": "SA", "Perth": "WA", "Canberra": "ACT", "Tasmania": "TAS", "Hobart": "TAS", "Launceston": "TAS",
    "Darwin": "NT", "Auckland": "NZ", "Wellington": "NZ", "Christchurch": "NZ", "Hamilton": "NZ", "Dunedin": "NZ",
    "Port Moresby": "PNG", "Fiji": "FJ",
}
# Name patterns, checked in order (state bodies and venues: "Netball Queensland", "Optus Stadium", "Eden Park")
NAME_STATE = [
    ("NZ", r"new zealand|\bnz\b|aotearoa|auckland|wellington|christchurch|eden park|sky stadium|hagley oval|silver ferns|all blacks|black ?caps|tall blacks|super smash|round the bays|super rugby pacific|anz premiership|waikato|otago|dunedin|bay of plenty|taranaki"),
    ("WA", r"\bwa\b|western australia|perth|fremantle|optus stadium|rac arena|hbf park|wa cricket|waca\b|rottnest"),
    ("TAS", r"tasmania|\btas\b|hobart|launceston|blundstone arena|ninja stadium|utas stadium|york park"),
    ("NT", r"northern territory|\bnt\b|darwin|alice springs|tio stadium"),
    ("SA", r"south australia|\bsa\b|adelaide|sanfl|adelaide oval|coopers stadium"),
    ("ACT", r"\bact\b|canberra|manuka|gio stadium"),
    ("QLD-REG", r"townsville|cairns|north queensland|mackay|rockhampton|toowoomba|queensland country bank stadium"),
    ("QLD", r"queensland|\bqld\b|brisbane|gold coast|sunshine coast|gabba|suncorp stadium|ipswich|moreton bay|redcliffe"),
    ("NSW", r"\bnsw\b|new south wales|sydney|newcastle|wollongong|parramatta|penrith|illawarra|accor stadium|allianz stadium|afterpay arena|qudos bank arena|commbank stadium|scg\b|sydney cricket ground|homebush|bathurst|mount panorama|venues nsw|royal randwick|rosehill"),
    ("VIC", r"victoria\b|victorian|\bvic\b|melbourne|geelong|ballarat|bendigo|mcg\b|marvel stadium|aami park|rod laver|kardinia|flemington|moonee valley|phillip island|australian open|australian grand prix"),
]


def state_of(slug, name="", domain="", city=None):
    """Market code for a property ("VIC", "NSW", "QLD", "QLD-REG", "SA", "WA", "TAS", "NT", "ACT", "NZ", ...), or
    None for national bodies, overseas properties and anything we can't place. None never blocks a match."""
    import re
    c = city or CITY.get(slug)
    if c in CITY_STATE:
        return CITY_STATE[c]
    if (domain or "").endswith(".nz") or ".nz/" in (domain or ""):
        return "NZ"
    t = (name or slug or "").lower()
    for code, rx in NAME_STATE:
        if re.search(rx, t):
            return code
    return None
