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
