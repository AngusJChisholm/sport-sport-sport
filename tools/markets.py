"""Tags every deal in deals.json with a "market": where the property (the rights holder) is based.

  Australia, New Zealand              home markets (region "ANZ")
  North America, UK & Ireland         core markets
  Europe, Asia, Middle East,
  Rest of World                       watch markets (Rest of World = Latin America, Africa, the Caribbean)
  Global                              properties that are worldwide by nature: FIFA, the IOC, F1, UEFA Champions
                                      League, ICC, World Rugby, ATP/WTA tours and the like

Rules:
  - Tag by the property's home, never the brand's. Toyota x NFL Melbourne Game is Australia.
  - An Australian brand on an overseas property goes to the property's market (National Storage x LA Rams is
    North America), so "region" ANZ doesn't always mean market Australia or New Zealand.
  - "region" (ANZ / Global) stays as it is: the scans, SSS Pro and Instagram still use it.

Overrides: set "market" on a property in entities.json (e.g. "market": "Asia") and every deal for it follows.
Set "marketLock": true on a deal to keep a market set by hand.

Run: python3 tools/markets.py          fills deals with no market yet
     python3 tools/markets.py --all    re-tags everything (after changing the rules)
     python3 tools/markets.py --report prints anything that fell through to a fallback
"""
import json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from locations import state_of  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MARKETS = ["Australia", "New Zealand", "North America", "UK & Ireland", "Europe", "Asia", "Middle East",
           "Rest of World", "Global"]


def rx(*words):
    return re.compile(r"(?<![\w])(?:" + "|".join(words) + r")(?![\w])", re.I)


# Checked in this order against the property side of the deal (then its summary). First hit wins.
GLOBAL = rx(r"fifa", r"world cup", r"club world cup", r"\bioc\b", r"olympics?", r"olympic games", r"paralympics?",
            r"la28", r"brisbane 2032", r"milano cortina", r"formula 1", r"\bf1\b", r"f1 academy", r"formula e",
            r"motogp", r"world superbikes?", r"\bwrc\b", r"world rally", r"world endurance", r"\bwec\b",
            r"uefa champions league", r"champions league", r"\bicc\b", r"world rugby", r"rugby world cups?",
            r"\batp\b", r"\bwta\b", r"\bitf\b", r"davis cup", r"billie jean king cup", r"united cup",
            r"world athletics", r"diamond league", r"ironman", r"world triathlon", r"\bufc\b", r"\bwwe\b",
            r"\bpfl\b", r"one championship", r"\bfiba\b", r"world aquatics", r"\buci\b", r"world surf league",
            r"\bwsl\b(?! women)", r"sailgp", r"america'?s cup", r"hyrox(?! north america)", r"\bliv golf\b",
            r"\bitf\b", r"commonwealth games", r"world baseball classic", r"\bfivb\b", r"world padel",
            r"premier padel", r"\bwtt\b(?! world team)", r"world table tennis", r"\bbwf\b", r"esl", r"blast",
            r"\bpgl\b", r"riot games", r"valorant champions", r"league of legends", r"esports world cup",
            r"world snooker", r"world chess", r"\bfide\b", r"red bull racing", r"mclaren", r"ferrari",
            r"mercedes(?:-amg)? (?:f1|petronas)", r"williams racing", r"aston martin (?:f1|aramco)", r"alpine f1",
            r"haas", r"sauber", r"audi f1", r"cadillac f1", r"racing bulls", r"visa cash app rb",
            r"world masters", r"special olympics", r"world games", r"le mans")

NZ = re.compile(r"new zealand|\bnz\b|aotearoa|auckland|wellington|christchurch|hamilton|dunedin|otago|canterbury"
                r"|waikato|taranaki|bay of plenty|hawke'?s bay|northland|eden park|sky stadium|all blacks"
                r"|black ?ferns|black ?caps|white ferns|silver ferns|tall blacks|tall ferns|super smash"
                r"|anz premiership|\bnpc\b|blues|chiefs(?<!png chiefs)|crusaders|highlanders|hurricanes(?! poua)"
                r"|hurricanes poua|matat|moana pasifika|warriors|breakers|phoenix|auckland fc|fijian drua"
                r"|tactix|mystics|magic|pulse|stars netball|steel", re.I)

NA = rx(r"nfl", r"nba", r"wnba", r"mlb", r"nhl", r"mls", r"nwsl", r"usl", r"nascar", r"indycar", r"imsa",
        r"pga tour", r"lpga", r"tgl", r"wtgl", r"us open", r"usta", r"ncaa", r"ufl", r"pll", r"\bpwhl\b",
        r"world team tennis", r"big ten", r"\bsec\b", r"\bacc\b", r"big 12", r"pac-12", r"athletics",
        r"college", r"university", r"super bowl", r"kentucky derby", r"breeders'? cup",
        r"usa", r"u\.s\.", r"united states", r"america(?:n)?", r"canada", r"canadian", r"team usa",
        r"monumental", r"madison square", r"msg", r"hyrox north america", r"major league", r"pickleball",
        r"ppa tour", r"mlp", r"cricket usa", r"major league cricket", r"concacaf", r"gold cup",
        # cities and states
        r"new york", r"brooklyn", r"boston", r"philadelphia", r"76ers", r"chicago", r"los angeles", r"la ",
        r"san francisco", r"golden state", r"seattle", r"portland", r"denver", r"dallas", r"houston", r"austin",
        r"san antonio", r"miami", r"orlando", r"tampa", r"atlanta", r"charlotte", r"nashville", r"memphis",
        r"new orleans", r"detroit", r"cleveland", r"cincinnati", r"columbus", r"pittsburgh", r"baltimore",
        r"washington", r"minnesota", r"milwaukee", r"kansas city", r"st\.? louis", r"indiana", r"indianapolis",
        r"phoenix suns", r"arizona", r"las vegas", r"vegas", r"utah", r"salt lake", r"sacramento",
        r"san diego", r"oklahoma", r"carolina", r"jacksonville", r"buffalo", r"green bay", r"new england",
        r"new jersey", r"toronto", r"montreal", r"vancouver", r"calgary", r"edmonton", r"ottawa", r"winnipeg",
        r"texas", r"florida", r"california", r"ohio", r"michigan", r"tennessee", r"alabama", r"georgia tech",
        r"kentucky", r"oregon", r"wisconsin", r"iowa", r"nebraska", r"virginia", r"louisiana", r"lsu",
        r"notre dame", r"stanford", r"\bcal\b", r"ucla", r"usc", r"fsu", r"unlv", r"rice",
        # club names that don't carry a city
        r"lakers", r"celtics", r"knicks", r"warriors(?= .*nba)", r"bucks", r"suns", r"heat", r"nets", r"bulls",
        r"cowboys(?! .*north queensland)", r"texans", r"chiefs(?= .*nfl)", r"packers", r"eagles(?= .*nfl)",
        r"steelers", r"49ers", r"yankees", r"dodgers", r"red sox", r"cubs", r"mets", r"oilers", r"maple leafs",
        r"canadiens", r"bruins", r"rangers(?= .*nhl)", r"inter miami", r"lafc", r"la galaxy", r"23xi",
        r"hendrick", r"penske", r"joe gibbs", r"fenway", r"wrexham(?= .*usa)")

UK = rx(r"premier league", r"\bepl\b", r"\befl\b", r"championship", r"league one", r"league two",
        r"\bwsl\b women", r"women'?s super league", r"fa cup", r"carabao", r"the fa\b", r"england", r"english",
        r"scotland", r"scottish", r"wales", r"welsh", r"ireland", r"irish", r"northern ireland", r"britain",
        r"british", r"\buk\b", r"\brfu\b", r"premiership rugby", r"gallagher", r"\burc\b", r"six nations",
        r"the hundred", r"county cricket", r"\becb\b", r"lord'?s", r"\bmcc\b", r"wimbledon", r"all england",
        r"the open", r"r&a", r"ryder cup", r"dp world tour", r"\bgaa\b", r"gaelic", r"silverstone",
        r"grand national", r"aintree", r"ascot", r"cheltenham", r"london", r"manchester", r"liverpool",
        r"everton", r"arsenal", r"chelsea", r"tottenham", r"spurs", r"newcastle united", r"sunderland",
        r"aston villa", r"west ham", r"brighton", r"crystal palace", r"fulham", r"brentford", r"wolves",
        r"wolverhampton", r"nottingham", r"leicester", r"leeds", r"southampton", r"bournemouth", r"burnley",
        r"ipswich", r"sheffield", r"birmingham", r"wrexham", r"portsmouth", r"middlesbrough", r"norwich",
        r"coventry", r"stoke", r"derby", r"hull", r"swansea", r"cardiff", r"celtic", r"rangers(?! .*nhl)",
        r"aberdeen", r"hearts", r"hibernian", r"bath rugby", r"saracens", r"harlequins", r"leinster",
        r"munster", r"ulster", r"connacht", r"edinburgh", r"glasgow", r"surrey", r"yorkshire", r"lancashire",
        r"jersey mike'?s.*efl", r"lionesses", r"red roses", r"british & irish lions", r"lions tour",
        r"team gb", r"\bbbc\b", r"sky sports", r"premier league darts", r"\bpdc\b")

EU = rx(r"uefa", r"europa league", r"conference league", r"euro 20\d\d", r"euros?", r"european", r"europe",
        r"la ?liga", r"laliga", r"serie a", r"bundesliga", r"ligue 1", r"eredivisie", r"primeira liga",
        r"liga portugal", r"super lig", r"süper lig", r"euroleague", r"eurocup", r"tour de france",
        r"giro", r"vuelta", r"roland[- ]garros", r"french open", r"ehf", r"handball", r"top 14", r"\bffr\b",
        r"ffp", r"\bdfb\b", r"\brfef\b", r"\bfigc\b", r"\bknvb\b", r"real madrid", r"barcelona", r"barça",
        r"atl[eé]tico", r"sevilla", r"valencia", r"villarreal", r"athletic club", r"real sociedad", r"betis",
        r"juventus", r"inter(?: milan)?(?! miami)", r"ac milan", r"milan", r"napoli", r"roma", r"lazio",
        r"atalanta", r"fiorentina", r"bayern", r"dortmund", r"leverkusen", r"leipzig", r"eintracht",
        r"schalke", r"wolfsburg", r"stuttgart", r"psg", r"paris saint-germain", r"paris", r"marseille",
        r"lyon", r"monaco", r"lille", r"toulouse", r"nice", r"benfica", r"porto", r"sporting", r"ajax", r"psv",
        r"feyenoord", r"galatasaray", r"fenerbah[cç]e", r"be[sş]ikta[sş]", r"celtic(?= .*europe)",
        r"club brugge", r"anderlecht", r"olympiacos", r"panathinaikos", r"red star", r"dinamo",
        r"copenhagen", r"salzburg", r"basel", r"young boys", r"shakhtar", r"france", r"french", r"germany",
        r"german", r"spain", r"spanish", r"italy", r"italian", r"portugal", r"netherlands", r"dutch",
        r"belgium", r"switzerland", r"swiss", r"austria", r"sweden", r"norway", r"denmark", r"finland",
        r"poland", r"czech", r"greece", r"turkey", r"türkiye", r"croatia", r"serbia", r"hungary",
        r"1905 gsyiad", r"alpine canada(?<!.)", r"monza", r"spa-francorchamps", r"kitzb[uü]hel")

ME = rx(r"saudi", r"\bksa\b", r"riyadh", r"jeddah", r"diriyah", r"neom", r"\buae\b", r"emirates(?! stadium)",
        r"dubai", r"abu dhabi", r"sharjah", r"qatar", r"doha", r"bahrain", r"kuwait", r"oman", r"muscat",
        r"jordan", r"egypt", r"al[- ]nassr", r"al[- ]hilal", r"al[- ]ittihad", r"al[- ]ahli", r"al[- ]qadsiah",
        r"al[- ]ain", r"al[- ]sadd", r"spl\b", r"roshn", r"yas marina", r"lusail", r"ilt20", r"dp world ilt20",
        r"dubai t100", r"6 kings slam", r"esports world cup foundation(?<!.)")

ASIA = rx(r"india", r"indian", r"bcci", r"\bipl\b", r"\bwpl\b", r"isl", r"pro kabaddi", r"kabaddi",
          r"mumbai", r"chennai", r"kolkata", r"delhi", r"bengaluru", r"bangalore", r"hyderabad", r"punjab",
          r"rajasthan", r"gujarat", r"lucknow", r"japan", r"japanese", r"j\.?league", r"b\.?league", r"npb",
          r"tokyo", r"osaka", r"yokohama", r"kyoto", r"china", r"chinese", r"\bcsl\b", r"cba", r"shanghai",
          r"beijing", r"hong kong", r"macau", r"korea", r"korean", r"k league", r"kbo", r"seoul", r"singapore",
          r"malaysia", r"kuala lumpur", r"indonesia", r"jakarta", r"thailand", r"thai", r"bangkok",
          r"philippines", r"manila", r"vietnam", r"taiwan", r"pakistan", r"\bpsl\b", r"pcb", r"lahore",
          r"karachi", r"sri lanka", r"slc", r"bangladesh", r"\bbpl\b", r"nepal", r"\bafc\b", r"asian games",
          r"asia cup", r"asian", r"asia", r"lanka premier league", r"suzuka", r"marina bay")

ROW = rx(r"brazil", r"brazilian", r"flamengo", r"corinthians", r"palmeiras", r"santos", r"são paulo",
         r"sao paulo", r"argentina", r"boca juniors", r"river plate", r"mexico", r"mexican", r"liga mx",
         r"chivas", r"club am[eé]rica", r"tigres", r"monterrey", r"colombia", r"chile", r"peru", r"uruguay",
         r"conmebol", r"copa libertadores", r"copa am[eé]rica", r"south africa", r"springboks", r"proteas",
         r"\bsa20\b", r"kenya", r"nigeria", r"ghana", r"morocco", r"africa", r"african", r"\bcaf\b",
         r"caribbean", r"\bcpl\b", r"west indies", r"cricket west indies", r"jamaica", r"trinidad",
         r"barbados", r"bulls(?= .*urc)", r"stormers", r"sharks(?= .*urc)", r"interlagos")

# Named properties and athletes the patterns can't place (athletes go where they play, tour athletes are Global).
NAMED = {
    "_first": [],
    "Australia": ["nrl", "national pickleball league", "sbs", "a-leagues", "macarthur fc", "cricket nsw", "rugby wa", "basketball wa", "hockey one",
                  "tennis nsw", "shyla heal", "invictus games australia"],
    "UK & Ireland": ["salford city", "west bromwich", "watford", "luton town", "peterborough", "bromley",
                     "blackburn rovers", "charlton", "reading", "ccc", "northamptonshire", "somerset", "spfl",
                     "pgmol", "pfa", "prem rugby", "premiership women's rugby", "lta", "wrexham", "wembley", "the o2",
                     "baller league", "cole palmer", "jack grealish", "dominik szoboszlai", "florian wirtz"],
    "Europe": ["como 1907", "torino", "udinese", "sivasspor", "copa del rey", "croatian", "fis", "four hills",
               "epcr", "canyon-sram", "a.s.o.", "liga f", "ekstraklasa", "olympique lyonnais", "vendée",
               "cska sofia", "el clásico", "portuguese", "turkish", "hotelplanner tour", "premier jumping league",
               "lamine yamal", "kylian mbappé", "achraf hakimi", "eden hazard", "luis figo", "jürgen klopp"],
    "North America": ["unrivaled", "connecticut sun", "gotham fc", "us soccer", "dickies arena", "l.a. live",
                      "aeg", "top rank", "athletes unlimited", "missouri", "x games", "rally us",
                      "supermotocross", "trackhouse", "usga", "us sailing", "bnp paribas open", "stockton kings",
                      "churchill downs", "tmrw", "national squash league", "formula drift", "jake paul", "grand slam of curling",
                      "angel reese", "a'ja wilson", "caitlin clark", "cameron brink", "madison booker",
                      "stephen curry", "nyjah huston", "garrett smithley", "pga"],
    "Asia": ["chennaiyin", "mohun bagan", "odisha", "northeast united", "aiff", "up warriorz", "jharkhand",
             "afghanistan", "asean", "inspire arena", "mpbl", "jiostar", "s8ul", "8bit", "iqoo soul", "pgti",
             "ultimate table tennis", "smriti mandhana", "yashasvi jaiswal", "rishabh pant", "jasprit bumrah",
             "sachin tendulkar", "kl rahul", "manu bhaker", "vikram pratap singh", "kim ye-ji"],
    "Middle East": ["al ahly"],
    "Rest of World": ["argentine", "arena fonte nova", "sa rugby", "namibia", "liga profesional", "brasil",
                      "acapulco", "mi cape town", "trinbago", "chris gayle"],
    "Global": ["fia", "world archery", "world sailing", "world gymnastics", "global gymnastics", "ihf", "isu",
               "fih", "professional squash association", "t100", "laver cup", "invictus games",
               "esports nations cup", "e1 series", "extreme h", "ea sports", "team vitality", "nrg", "williams",
               "jaguar tcs racing", "total chess", "gresini", "ktm", "international luge", "biathlon",
               "volleyball nations league", "conor mcgregor", "charles leclerc", "david beckham", "a$ap rocky", "prime video"],
}
# Checked before everything else: names that would otherwise trip a broader pattern ("Indian Wells", "New
# England Patriots", "Pakistan Super League").
FIRST = [("North America", ["new york", "texas rangers", "indian wells", "new england patriots", "new mexico", "atlético dallas",
                            "laliga north america"]),
         ("Asia", ["indian olympic", "pakistan super league", "indian super league", "mongolian",
                   "japanese olympic", "hyrox india", "shizuoka"]),
         ("Europe", ["french olympic", "cyprus olympic", "basketball champions league"]),
         ("Middle East", ["dubai t100", "dubai world cup"]),
         ("UK & Ireland", ["special olympics gb"]),
         ("Australia", ["suncorp stadium"])]
NAMED.pop("_first")
NAMED_RX = [(m, rx(*[re.escape(w) for w in ws])) for m, ws in FIRST + list(NAMED.items())]

TLD = [(r"\.com\.au$|\.au$", "Australia"), (r"\.nz$", "New Zealand"), (r"\.ca$|\.us$", "North America"),
       (r"\.uk$|\.ie$|\.scot$|\.wales$", "UK & Ireland"),
       (r"\.(de|fr|es|it|nl|pt|be|ch|at|se|no|dk|fi|pl|cz|gr|tr|hr|rs|hu|ro|eu|cat|lu|si|sk)$", "Europe"),
       (r"\.(sa|ae|qa|bh|kw|om|jo|eg)$", "Middle East"),
       (r"\.(in|jp|cn|kr|sg|hk|my|id|th|ph|vn|tw|pk|lk|bd|np)$", "Asia"),
       (r"\.(br|ar|mx|co|cl|pe|uy|za|ke|ng|gh|ma|jm|tt|bb)$", "Rest of World")]

SPORT_NA = {"NFL", "Baseball", "Ice hockey", "College sport", "Bull riding", "Pickleball"}


def split(deal):
    p = re.split(r"\s+[×x]\s+", str(deal or ""))
    return (p[0].strip(), " × ".join(p[1:]).strip()) if len(p) >= 2 else ("", str(deal or "").strip())


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def host(url):
    m = re.match(r"https?://([^/]+)", url or "")
    return (m.group(1).lower().removeprefix("www.") if m else "")


ORDER = [("Global", GLOBAL), ("Middle East", ME), ("Asia", ASIA), ("Rest of World", ROW), ("UK & Ireland", UK),
         ("Europe", EU), ("North America", NA)]


def market_of(d, overrides):
    brand, prop = split(d.get("deal"))
    for part in re.split(r"\s+/\s+", prop):
        m = overrides.get(slug(part))
        if m:
            return m, "override"
    sport = d.get("sport") or ""
    if d.get("region") == "ANZ":
        st = state_of(slug(prop), prop, host(d.get("url")))
        if st == "NZ":
            return "New Zealand", "rule"
        if st:
            return "Australia", "rule"
        if NZ.search(prop):
            return "New Zealand", "rule"
        # ANZ brand on an overseas property (National Storage x LA Rams): tag the property's own market.
        # Global events held here (Rugby World Cup 2027, United Cup) and deals tied to a local game (NFL
        # Melbourne) stay Australian.
        local = r"australia|oceania|australasia|aussie|melbourne|sydney|brisbane|perth|adelaide|new zealand|\banz\b|home soil"
        if not re.search(local, prop + " " + (d.get("summary") or ""), re.I):
            for name, pat in NAMED_RX + ORDER:
                if pat.search(prop):
                    return (name, "rule") if name != "Global" else ("Australia", "rule")
        return "Australia", "rule"
    if sport == "Rugby league" and re.search(r"\bsuper league\b", prop, re.I):
        return "UK & Ireland", "rule"
    for name, pat in NAMED_RX:
        if pat.search(prop):
            return name, "rule"
    # Non-ANZ: the property name decides first, then the source's own country domain, then the summary.
    for name, pat in ORDER:
        if pat.search(prop):
            return name, "rule"
    if sport in SPORT_NA:
        return "North America", "rule"
    h = host(d.get("url"))
    for pat, name in TLD:
        if re.search(pat, h):
            return name, "tld"
    summ = d.get("summary") or ""
    for name, pat in ORDER:
        if name not in ("Global", "North America") and pat.search(summ):
            return name, "summary"
    if sport in {"Motorsport", "Esports", "Olympics", "Golf", "Tennis", "MMA"}:
        return "Global", "fallback"
    return "Global", "unknown"


def main():
    redo, report = "--all" in sys.argv, "--report" in sys.argv
    path = ROOT / "deals.json"
    data = json.loads(path.read_text())
    ents = json.loads((ROOT / "entities.json").read_text()).get("entities", {})
    overrides = {k: v["market"] for k, v in ents.items() if isinstance(v, dict) and v.get("market") in MARKETS}
    changed, how, miss = 0, Counter(), []
    for d in data["deals"]:
        if d.get("marketLock") or (d.get("market") and not redo):
            continue
        m, why = market_of(d, overrides)
        how[why] += 1
        if why in ("unknown", "fallback", "summary"):
            miss.append((why, m, d.get("deal"), d.get("sport")))
        if d.get("market") != m:
            d["market"] = m
            changed += 1
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"markets: {changed} changes", dict(how))
    print(Counter(d.get("market") for d in data["deals"]).most_common())
    if report:
        for r in sorted(miss):
            print(*r, sep=" | ")


if __name__ == "__main__":
    main()
