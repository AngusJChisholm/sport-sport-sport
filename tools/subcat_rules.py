"""Sub-categories for brands, used by SSS Pro's Match Score (tools/match.py).

A broad category like "Alcohol" is too blunt for clash checks: the AO has a beer, a champagne and a vodka
partner at once. Each brand gets a sub-category from its name and website, inside its main category.
Set "sub" on a brand in entities.json to override. A brand with no rule match gets None, and None never
blocks a match (we only block when we're sure two brands are in the same slot).
"""
import re

SUBS = {
    "Alcohol": [
        ("Champagne & sparkling", r"champagne|moet|chandon|mumm|piper|veuve|taittinger|bollinger|laurent-perrier|perrier-jou|krug|dom perignon|prosecco|sparkling"),
        ("Spirits", r"vodka|gin\b|rum\b|whisk|bourbon|tequila|mezcal|grey goose|absolut|smirnoff|belvedere|altos|olmeca|jameson|johnnie walker|jim beam|jack daniel|canadian club|bundaberg rum|bacardi|hennessy|aperol|campari|baileys|jagermeister|four pillars|archie rose|diageo|pernod|luzhou|baijiu|spirit"),
        ("Wine", r"wine|wines|winery|estate|penfolds|jacob's creek|wolf blass|yellow tail|de bortoli|brown brothers|cobram estate|treasury|accolade|vineyard|cellar"),
        ("Beer & cider", r"beer|brew|lager|ale\b|cider|carlton|vb\b|victoria bitter|xxxx|great northern|hahn|tooheys|james squire|coopers|heineken|corona|stella|budweiser|bud light|michelob|guinness|asahi|kirin|carlsberg|peroni|furphy|balter|4 pines|somersby|lion\b|cub\b|seltzer|hard solo|pure blonde|tiger beer|sapporo"),
        ("Liquor retail", r"dan murphy|bws\b|first choice|liquorland|endeavour"),
    ],
    "Non-alcoholic drinks": [
        ("Energy drinks", r"red bull|monster|v energy|celsius|rockstar|guru|prime energy|mother\b"),
        ("Sports & hydration", r"gatorade|powerade|electrolit|liquid i\.?v|hydralyte|prime|bodyarmor|lucozade|hydration|electrolyte|sports drink"),
        ("Water", r"water|mount franklin|cool ridge|fiji|evian|san pellegrino|waterdrop"),
        ("Coffee & tea", r"coffee|nespresso|lavazza|starbucks|vittoria|campos|luckin|nescafe|tea\b|lipton|t2\b|twinings"),
        ("Dairy & milk", r"milk|dairy|a2\b|devondale|pauls|milo|up&go|yopro|chobani|bega"),
        ("Soft drinks", r"coca-cola|coke\b|pepsi|schweppes|kirks|solo\b|sprite|fanta|bundaberg|sodastream|soft drink|kombucha|juice"),
    ],
    "Food & nutrition": [
        ("Food delivery", r"doordash|uber eats|menulog|deliveroo|hellofresh|youfoodz|marley spoon|dinnerly|my muscle chef"),
        ("Quick service food", r"mcdonald'?s|maccas|kfc|hungry jack|burger king|domino|pizza|subway|guzman|grill'd|nando|red rooster|oporto|zambrero|el jannah|jersey mike|chicken|taco"),
        ("Snacks & confectionery", r"cadbury|mondelez|mars\b|wrigley|chocolate|lolly|lollies|confection|smith's|doritos|pringles|lay's|frito|arnott|snack|allen's|natural confectionery|m&m|snickers|kitkat"),
        ("Supplements & protein", r"protein|supplement|bulk nutrients|optimum nutrition|musashi|ehp|myprotein|vitamin|ezz"),
        ("Packaged food", r"nestle|kellogg|uncle tobys|weet-bix|sanitarium|heinz|maggi|masterfoods|old el paso|mccain|continental|bakery|bread|tip top|cereal|meat|beef|lamb|pork|seafood|steggles|ingham|ice cream|streets|peters|bulla|food"),
    ],
    "Banking & finance": [
        ("Payments & cards", r"visa\b|mastercard|american express|amex|paypal|afterpay|zip\b|klarna|eftpos|square|tyro"),
        ("Super & wealth", r"super\b|superannuation|aware super|hostplus|australiansuper|cbus|unisuper|rest\b|wealth|asset management|investment|capital|funds|eqt\b"),
        ("Banks", r"bank|westpac|anz\b|nab\b|commbank|commonwealth|bendigo|macquarie|suncorp bank|ing\b|ubank|bankwest|bank of|hsbc|barclays|lloyds|santander|bbva|ubs|citi|credit union|mortgage|lending|loans"),
    ],
    "Insurance": [
        ("Health insurance", r"bupa|medibank|hcf|nib\b|hbf|ahm|cbhs|health fund|health insurance|gmhba|teachers health|westfund|frank health"),
        ("Life insurance", r"\btal\b|aia\b|life insurance|zurich life|mlc"),
        ("General insurance", r"aami|nrma|racv|racq|allianz|axa|zurich|generali|youi|budget direct|suncorp|qbe|iag\b|gio\b|chubb|1cover|real insurance|howden|jab insurance|insurance|insurer|broker"),
    ],
    "Automotive": [
        ("Tyres", r"tyre|tire|bridgestone|pirelli|michelin|goodyear|continental|beaurepaires|kumho|hankook|yokohama|tyrepower"),
        ("Oils & parts", r"oil\b|castrol|penrite|mobil|valvoline|repco|supercheap|parts|bosch car|ngk|niterra|ntk|midas"),
        ("Motorcycles", r"yamaha|ducati|ktm|harley|kawasaki|husqvarna|triumph|royal enfield|hero vida|hero moto|aprilia|vespa|suzuki moto"),
        ("Car dealers", r"motors\b|motor group|dealer|autos\b|village motors|sci-fleet|motor scout|autograb|carsales|car ?finance"),
        ("Car makers", r"^(toyota|hyundai|kia|ford|holden|mazda|nissan|honda|subaru|mitsubishi|isuzu|gwm|great wall|haval|byd|tesla|bmw|mercedes|mercedes-benz|audi|volkswagen|vw|skoda|porsche|ferrari|lamborghini|cupra|seat|volvo|polestar|jeep|ram|chevrolet|cadillac|lexus|genesis|mg|ldv|chery|omoda|jaecoo|kgm|ssangyong|gac|zeekr|xpeng|nio|leapmotor|renault|peugeot|citroen|suzuki|land rover|range rover|jaguar|mini|alfa romeo|fiat|maserati|aston martin|bentley|rolls-royce|mclaren automotive|lotus|deepal|smart|geely|lynk|tank|mahindra|tata motors)( (australia|new zealand|nz|motor corporation|motor company|motors|cars|automotive|group))?$"),
    ],
    "Airlines & travel": [
        ("Airlines", r"airline|airways|qantas|jetstar|virgin|air new zealand|emirates|etihad|qatar|singapore airlines|cathay|turkish|delta|united airlines|american airlines|lufthansa|air france|klm|riyadh air|saudia|fly|aviation|flexjet|netjets"),
        ("Hotels & resorts", r"hotel|resort|accor|marriott|hilton|hyatt|ihg|sheraton|novotel|crown towers|bonvoy"),
        ("Travel booking", r"booking|expedia|airbnb|travel|cruise|flight centre|webjet|wotif|trivago|luxury escapes|stoked"),
        ("Airports", r"airport"),
    ],
    "Technology": [
        ("Social & content platforms", r"tiktok|meta\b|facebook|instagram|snapchat|youtube|x corp|twitter|reddit|pinterest|twitch|overtime"),
        ("Wearables & health tech", r"oura|whoop|garmin|fitbit|polar\b|coros|apple watch|wearable|smart ring"),
        ("Consumer electronics", r"samsung|lg\b|sony|panasonic|philips|hisense|tcl|xiaomi|oppo|vivo\b|huawei|honor\b|oneplus|apple\b|jbl|bose|beats|gopro|dji|canon|nikon|logitech|razer|dyson|haier|electrolux"),
        ("IT services & consulting", r"infosys|accenture|ibm|cognizant|tcs\b|tata consultancy|wipro|hcl|capgemini|dxc|nec\b|fujitsu|deloitte digital|kpmg|pwc|ey\b|data#3|datacom|it services"),
        ("Cybersecurity", r"cyber|crowdstrike|kaspersky|bitdefender|fortinet|palo alto|norton|mcafee|okta|darktrace"),
        ("Sports data & tech", r"sportradar|genius sports|stats perform|hawk-eye|catapult|sofascore|second spectrum|playmaker"),
        ("Software & cloud", r"google|alphabet|microsoft|amazon web|aws|oracle|salesforce|sap\b|adobe|atlassian|canva|xero|myob|zoom|slack|databricks|snowflake|cloud|software|workday|servicenow|dropbox|docusign"),
        ("AI", r"openai|chatgpt|anthropic|\bai\b|artificial intelligence|firmus|nvidia"),
    ],
    "Media & broadcast": [
        ("Streaming & audio", r"spotify|apple music|netflix|prime video|stan\b|kayo|binge|dazn|paramount\+|disney\+|podcast|stream"),
        ("Radio", r"radio|triple m|nova\b|austereo|hit network|arn\b|kiis|gold 1|sen\b|southern cross"),
        ("Publishing & news", r"news corp|herald|newspaper|publishing|magazine|news\.com|daily telegraph|the age|smh|vogue|leadstory"),
        ("Outdoor media", r"jcdecaux|qms|ooh|outdoor|billboard"),
        ("Broadcast TV", r"tv\b|television|channel|network|nine\b|seven\b|ten\b|foxtel|fox sports|abc\b|sbs\b|espn|sky\b|bein|tnt|nbc|cbs|bbc|itv|sport 24|optus sport"),
    ],
    "Hospitality & entertainment": [
        ("Ticketing", r"ticketmaster|ticketek|axs\b|moshtix|eventbrite|oztix|seatgeek|stubhub|viagogo|ticket"),
        ("Casinos & hotels", r"crown|star entertainment|the star|skycity|casino|resorts"),
        ("Attractions & venues", r"dreamworld|movie world|wet n wild|luna park|gumbuya|zoo|aquarium|sea life|merlin|museum|theme park|venue|stadium"),
        ("Cinemas", r"cinema|hoyts|event cinemas|village|reading"),
        ("Pubs, bars & restaurants", r"restaurant|bar\b|pub\b|merivale|solotel|australian venue|alh\b|sporting globe|the pass|hospitality"),
        ("Live events & music", r"live nation|festival|concert|tour\b|fever|events"),
    ],
    "Health & beauty": [
        ("Pharmacy & medical", r"chemist|pharmacy|priceline|amcal|terry white|pharma|medical|hospital|pathology|abbvie|pfizer|novartis|gsk|sanofi|csl\b|cochlear|resmed|sonic|healius|ramsay|healthscope|dental|physio|optom|specsavers|opsm|hearing|audiology"),
        ("Fitness clubs", r"fitness first|anytime fitness|f45|goodlife|jetts|plus fitness|snap fitness|club lime|gym\b|fitness"),
        ("Vitamins & wellness", r"vitamin|blackmores|swisse|nature's way|elevit|wellness|ezz life"),
        ("Beauty & personal care", r"mecca|sephora|l'or|loreal|nivea|dove|rexona|gillette|old spice|lynx|colgate|oral-b|sensodyne|huggies|kleenex|unilever|procter|p&g|skincare|beauty|cosmetic|sunscreen|shampoo|deodorant|venus"),
    ],
    "Retail": [
        ("Supermarkets", r"woolworths|coles|aldi|iga\b|costco|foodworks|spar|tesco|sainsbury|walmart|carrefour|lidl"),
        ("Hardware & home", r"bunnings|mitre 10|ikea|home depot|lowe's|freedom|amart|fantastic furniture|beds|forty winks|koala|ecosa|mattress"),
        ("Electronics retail", r"harvey norman|jb hi-fi|the good guys|officeworks|best buy"),
        ("Sports retail", r"rebel|jd sports|foot ?locker|sports direct|dick's|academy sports|intersport|decathlon|bcf|anaconda|elite eleven"),
        ("Department & fashion retail", r"myer|david jones|kmart|target|big w|westfield|scentre|vicinity|stockland|mall"),
        ("Pharmacy retail", r"chemist warehouse|priceline"),
    ],
    "Apparel & footwear": [
        ("Kit supplier", r"^(nike|adidas|puma|asics|new balance|under armour|mizuno|kappa|umbro|macron|castore|hummel|joma|kelme|errea|le coq sportif|canterbury|classic sportswear|isc|iscsport|o'neills|oneills|oxen|oxen sport|alpha sport|burley|bla(c)?k|x-blades|reebok|fila|champion|li-ning|anta|peak|xtep|ozone|sekem|kombat|strauss|konqa|sylvia p teamwear|belgravia|saba|valour sport|oneills)( (australia|sport|sports|teamwear))?$"),
        ("Fashion & lifestyle", r"boss\b|hugo|ralph lauren|lacoste|tommy|zara|h&m|uniqlo|r\.?m\.? williams|gucci|prada|fred perry|country road|calvin klein|polo|superdry|cotton on|kookai|menswear|outfitters|ringers western|ariat|tony barlow|tradie"),
        ("Activewear & recovery", r"2xu|lululemon|lskd|gymshark|jaggad|skins|blackroll|on running|hoka|skechers|vuori|rhone"),
        ("Headwear & licensing", r"new era|47 brand|'47|fanatics|mitchell & ness"),
    ],
    "Energy & utilities": [
        ("Fuel & oil", r"ampol|bp\b|shell|chevron|exxon|aramco|petronas|totalenergies|eni\b|caltex|viva energy|petrol|fuel|7-eleven"),
        ("Renewables & solar", r"solar|renewable|wind|vestas|1komma5|tesla energy|hydro|battery"),
        ("Energy retail", r"^(agl|origin|origin energy|energyaustralia|alinta|alinta energy|red energy|lumo|lumo energy|simply energy|powershop|momentum energy|ovo|ovo energy|engie|tango|dodo power|globird|amber|amber electric|sumo|covau|powerclub|nectr|mojo|kogan energy|meridian|genesis energy|contact energy|mercury|trustpower|electric kiwi|flick|nova energy|iren|aurora energy|synergy|ergon|energex|jemena|actewagl|powerbay)$"),
    ],
    "Telco": [("Telco", r".")],
    "Tourism & government": [
        ("Public health & safety", r"\btac\b|healthway|department of health|road safety|think!|responsible gambling|love ?the ?game|transport|main roads|return and earn|containers for change|vicreturn|quit\b|sunsmart"),
        ("Destination & host government", r"."),
    ],
    "Watches & luxury": [
        ("Watches", r"rolex|tag heuer|omega|tissot|longines|hublot|richard mille|swatch|seiko|citizen|casio|tudor|breitling|iwc|patek|audemars|watch"),
        ("Jewellery", r"tiffany|cartier|bulgari|pandora|swarovski|michael hill|jewel"),
        ("Fashion houses", r"louis vuitton|lvmh|gucci|prada|dior|chanel|hermes|burberry|fendi|balenciaga"),
    ],
    "Betting & wagering": [
        ("Prediction markets", r"kalshi|polymarket|predict"),
        ("Lotteries", r"lott|lottery|allwyn"),
        ("Bookmakers", r"."),
    ],
    "Fintech, crypto & trading": [
        ("Crypto", r"crypto|bitcoin|coinbase|binance|bybit|okx|kraken|swyftx|coinjar|nexo|bitpanda|web3|blockchain"),
        ("Trading & investing", r"capital\.com|etoro|stake\b|commsec|selfwealth|plus500|ig\b|cmc|interactive brokers|trading"),
        ("Payments & BNPL", r"afterpay|zip\b|klarna|sumup|paze|stripe|revolut|wise\b"),
    ],
    "Sporting goods & equipment": [
        ("Balls & racquets", r"dunlop|wilson|head\b|babolat|yonex|slazenger|sherrin|steeden|gilbert|spalding|molten|mikasa|select|mitre|kookaburra|gray-nicolls|gm cricket|masuri|ball"),
        ("Golf", r"titleist|taylormade|callaway|ping\b|srixon|cobra|golf"),
        ("Bikes & cycling", r"shimano|specialized|trek|giant|cannondale|99 bikes|bike|cycl"),
        ("Drinkware & outdoor", r"hydro flask|yeti|stanley|camelbak|frank green"),
    ],
}


# Host state or country for destination brands. A property sells one host destination: the AO has Visit
# Victoria and the City of Melbourne, so Tourism WA or Destination NSW is a clash, not a gap.
STATE = [
    ("VIC", r"victoria|\bvic\b|\.vic\.|melbourne|ballarat|geelong|casey|bendigo"),
    ("NSW", r"\bnsw\b|\.nsw\.|new south wales|sydney|parramatta|newcastle"),
    ("QLD", r"queensland|\bqld\b|\.qld\.|gold coast|moreton bay|cairns|townsville|mackay|ipswich|sunshine coast|south bank"),
    ("WA", r"\bwa\b|\.wa\.|western ?australia|perth|fremantle|stirling"),
    ("SA", r"south australia|\bsa\b|\.sa\.|adelaide|playford"),
    ("TAS", r"tasmania|\btas\b|\.tas\.|launceston|hobart"),
    ("NT", r"\bnt\b|\.nt\.|northern ?territory|darwin"),
    ("ACT", r"\bact\b|\.act\.|canberra"),
    ("AUS", r"australian government|tourism australia|australia\.gov"),
]


def destination(name, domain=""):
    """Host state/country code for a destination brand, or the brand name itself if we can't tell
    (so two unknown destinations still count as different)."""
    t = f"{name or ''} {domain or ''}".lower()
    for code, rx in STATE:
        if re.search(rx, t):
            return code
    return (name or "").lower().strip()


def classify(name, domain="", cat=None):
    """Return the sub-category for a brand inside its main category, or None if we can't tell."""
    if not cat or cat not in SUBS:
        return None
    n = (name or "").lower().strip()
    t = f"{n} {domain or ''}".lower()
    for sub, rx in SUBS[cat]:
        # anchored rules (^...$, e.g. car makers, kit suppliers) are exact-name lists, so test the name alone:
        # with the domain tacked on, "toyota toyota.com" never matched and Toyota/Kia never clashed
        if rx == "." or re.search(rx, n if rx.startswith("^") else t):
            return sub
    return None
