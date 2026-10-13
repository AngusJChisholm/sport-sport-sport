"""One-off: add researched Jan to early Sept 2026 deals to deals.json (archive only, no articles)."""
import json
from pathlib import Path

SM = "https://sportsmintmedia.com/"
SP = "https://www.sportspro.com/"
MI = "https://www.mi-3.com.au/"
BT = "https://www.bandt.com.au/"

# (date or YYYY-MM, deal, sport, type, region, summary, url)
R = [
# ---- September (pre-posting)
("2026-09-04","Nike × London City Lionesses","Football","Kit supplier","Global","Owner Michele Kang says the shirt deal is worth more than some in the Premier League.",SP+"news/sponsorship-marketing/london-city-lionesses-nike-shirt-sponsorship-michele-kang-september-2026/"),
("2026-09-03","MyPlace × Penrith Panthers","NRL","Principal partner","ANZ","Principal partnership renewed for three more seasons.",BT+"spotlight-on-sponsors-afl-scores-record-audience-as-370m-fans-tune-in/"),
# ---- August
("2026-08-27","FPT × Chelsea","Football","Extension","Global","Partnership extended as Chelsea grows its commercial and digital program.",SM+"chelsea-extend-fpt-partnership-as-commercial-and-digital-strategy-expands/"),
("2026-08-27","EGYPTAIR × FC Barcelona","Football","Official partner","Global","Exclusive airline rights across Barça's teams.",SM+"egyptair-secures-exclusive-airline-rights-across-fc-barcelona-teams/"),
("2026-08-27","Sportradar × EuroLeague","Basketball","Data rights","Global","Data and audiovisual betting rights for EuroLeague and EuroCup through 2031.",SM+"sportradar-secures-euroleague-and-eurocup-data-av-betting-rights-through-2031/"),
("2026-08-27","Under Armour × Kaylee McKeown","Swimming","Athlete endorsement","ANZ","Three-year deal through to the LA 2028 Olympics.",BT+"spotlight-on-sponsors-under-armour-kaylee-mckeown-commit-to-the-2028-olympics/"),
("2026-08-27","Devil's Corner × Tasmania Devils","AFL","Official partner","ANZ","Official wine partner on a long-term deal.",BT+"spotlight-on-sponsors-under-armour-kaylee-mckeown-commit-to-the-2028-olympics/"),
("2026-08-27","Dan Murphy's × NFL","NFL","Official partner","ANZ","Official retail liquor partner in Australia.",BT+"spotlight-on-sponsors-under-armour-kaylee-mckeown-commit-to-the-2028-olympics/"),
("2026-08-27","The Sporting Globe × NFL","NFL","Official partner","ANZ","Official sports bar partner in Australia.",BT+"spotlight-on-sponsors-under-armour-kaylee-mckeown-commit-to-the-2028-olympics/"),
("2026-08-26","Uber × PGA TOUR","Golf","Official partner","Global","Dual roles covering rides and food delivery.",SM+"uber-lands-dual-pga-tour-sponsorship-roles-across-mobility-and-food-delivery/"),
("2026-08-25","Cromwell × Leicester City","Football","Back-of-shirt","Global","Back-of-shirt partner for 2026/27.",SM+"leicester-city-secure-cromwell-as-back-of-shirt-partner-for-2026-27-season/"),
("2026-08-25","Campbell's × NFL","NFL","Extension","Global","Partnership moves to Chunky Frozen Meals.",SM+"campbells-nfl-partnership-enters-new-era-with-chunky-frozen-meals/"),
("2026-08-21","PTP × Football Australia","Football","Extension","ANZ","Partnership extended after hitting ten years.",MI+"21-08-2026/football-australia-and-ptp-extend-partnership-10-year"),
("2026-08-19","Harvey Norman × Hoops Capital","Basketball","Extension","ANZ","Extended deal to grow basketball in NSW.",MI+"19-08-2026/harvey-norman-extends-partnership-hoops-capital-boost-basketball-nsw"),
("2026-08-18","Kookaburra × Cricket Australia","Cricket","Extension","ANZ","Official ball and equipment supplier through 2030, a relationship over 80 years old.","https://ministryofsport.com/cricket-australia-and-kookaburra-extend-long-standing-partnership-through-to-2030/"),
("2026-08-14","Anytime Fitness × Adelaide Crows","AFL","Official partner","ANZ","Official fitness partner.",MI+"14-08-2026/anytime-fitness-joins-adelaide-crows-official-fitness-partner"),
("2026-08-13","Chemist Warehouse × AFLW umpires","AFL","Partnership","ANZ","New deal backing AFLW umpires.",MI+"13-08-2026/chemist-warehouse-backs-aflw-umpires-new-sponsorship-deal"),
("2026-08-10","XTB × FC Porto","Football","Partnership","Global","Three-year deal focused on global fan engagement.",SM+"fc-porto-and-xtb-strike-three-year-deal-to-drive-global-fan-engagement/"),
("2026-08-10","adidas × Croatian Football Federation","Football","Kit supplier","Global","New federation partnership.",SM+"adidas-secures-croatia-partnership-as-federation-begins-new-commercial-era/"),
("2026-08-08","LONGi × FC Bayern","Football","Official partner","Global","International commercial partner.",SM+"fc-bayern-land-longi-as-latest-international-commercial-partner/"),
("2026-08-08","mycar Tyre & Auto × Melbourne Stars","Cricket","Major partner","ANZ","Joins the Stars as a major partner.",SM+"mycar-tyre-auto-joins-melbourne-stars-as-major-partner/"),
("2026-08-07","giffgaff × Formula E","Motorsport","Official partner","Global","Formula E's first B Corp partner.",SM+"formula-e-secures-first-b-corp-partner-as-giffgaff-joins-championship/"),
("2026-08-07","Polymarket × New York Yankees","Baseball","Partnership","Global","Prediction market expands its MLB footprint.",SM+"polymarket-expands-mlb-footprint-with-new-york-yankees-partnership/"),
("2026-08-06","Emirates × Arsenal","Football","Extension","Global","Stadium naming rights renewed in a UK£70m deal, partnership runs through 2033.",SP+"sponsorship-marketing/arsenal-emirates-stadium-renewal-70-million-shirt-august-2026/"),
("2026-08-04","Betway × Manchester United","Football","Training kit","Global","UK£20m training kit deal.",SP+"news/sponsorship-marketing/sponsorship/manchester-united-strike-uk20m-betway-training-kit-deal/"),
("2026-08-03","Corporate Traveller × Perth Bears","NRL","Official partner","ANZ","Coaches partner ahead of the 2027 debut.",MI+"03-08-2026/corporate-traveller-partners-perth-bears-coaches-partner-ahead-2027-nrl-debut"),
# ---- July
("2026-07-24","oOh!media × Cricket Australia","Cricket","Partnership","ANZ","Partner for the 2026-27 NRMA Insurance men's Test series.",MI+"24-07-2026/oohmedia-and-cricket-australia-partner-2026-27-nrma-insurance-mens-test-series"),
("2026-07-24","Harvey Norman / Westpac / KFC × NRLW","NRL","Broadcast sponsorship","ANZ","Renewed as sponsors of NRLW coverage on Foxtel and Kayo.",MI+"24-07-2026/harvey-norman-westpac-and-kfc-renew-sponsorship-2026-nrlw-season-foxtel-and-kayo-sports"),
("2026-07-23","ClickHouse × Fulham","Football","Official partner","Global","Flagship Premier League sponsorship through Fulham.",SM+"clickhouse-lands-flagship-premier-league-sponsorship-through-fulham-fc/"),
("2026-07-23","Albert × Los Angeles Lakers","Basketball","Jersey patch","Global","New Lakers jersey patch partner.",SM+"albert-secures-premium-lakers-jersey-patch-sponsorship/"),
("2026-07-23","Midnite × Middlesbrough","Football","Shirt sponsorship","Global","Front-of-shirt partner.",SM+"midnite-and-mr-vegas-secure-major-front-of-shirt-partnerships-with-middlesbrough-and-reading/"),
("2026-07-22","Hola Health × Cricket Australia","Cricket","Back-of-shirt","ANZ","Cricket Australia's first all-format back-of-shirt sponsor.",SM+"cricket-australia-unveils-first-ever-all-format-back-of-shirt-sponsorship-with-hola-health/"),
("2026-07-21","Spire Healthcare × Team GB","Olympics","Official partner","Global","Exclusive healthcare services partner.",SM+"spire-healthcare-becomes-exclusive-healthcare-services-partner-of-team-gb/"),
("2026-07-15","Visit Rwanda × Aston Villa","Football","Shirt sponsorship","Global","Principal shirt deal reported at UK£20m a year.",SP+"news/sponsorship-marketing/aston-villa-visit-rwanda-shirt-principal-sponsorship-july-2026/"),
("2026-07-14","Monster Energy × Big 12","College sport","Title sponsorship","Global","Entitlement deal across football and basketball.",SM+"big-12-lands-monster-energy-entitlement-deal-for-football-and-basketball/"),
("2026-07-13","JPMorganChase × Dallas Mavericks","Basketball","Jersey patch","Global","The bank's first-ever NBA jersey patch.",SM+"dallas-mavericks-land-jpmorganchase-in-first-ever-nba-jersey-patch-partnership/"),
("2026-07-13","Chery UK × AFC Bournemouth","Football","Official partner","Global","Official automotive partner.",SM+"afc-bournemouth-bring-in-chery-uk-as-official-automotive-partner/"),
("2026-07-10","Firefox × Wrexham AFC","Football","Partnership","Global","New commercial partner for Wrexham.",SM+"wrexham-afc-expand-commercial-portfolio-with-firefox-pact/"),
("2026-07-09","Youi × Rugby League World Cup 2026","Rugby league","Major partner","ANZ","Major partner of the 2026 World Cup.",MI+"09-07-2026/youi-secures-major-partnership-2026-rugby-league-world-cup"),
("2026-07","BKT × Big Bash League","Cricket","Extension","ANZ","BBL partnership extended and Cricket Australia deal renewed.","https://www.tyrepress.com/2026/07/bkt-extends-big-bash-league-partnership-renews-cricket-australia-deal/"),
# ---- June
("2026-06-30","Coca-Cola × FC Bayern","Football","Extension","Global","Partnership extended past 50 years.",SM+"fc-bayern-and-coca-cola-extend-landmark-partnership-beyond-50-years/"),
("2026-06-30","Fanatics × Sheffield United","Football","Retail partner","Global","Retail and merchandise partnership.",SM+"sheffield-united-strengthen-retail-strategy-with-fanatics-partnership/"),
("2026-06-27","IREN × Golden State Warriors","Basketball","Jersey patch","Global","Record-breaking jersey patch deal.",SM+"golden-state-lands-record-breaking-jersey-sponsorship-deal-with-iren/"),
("2026-06-26","Zscaler × Aston Martin F1","Motorsport","Official partner","Global","Cybersecurity partner for the F1 team.",SM+"aston-martin-aramco-taps-zscaler-to-secure-next-generation-formula-1-operations/"),
("2026-06-26","Legora × Chelsea","Football","Official partner","Global","Official partner on a long-term deal.",SM+"chelsea-fc-onboard-legora-as-official-partner-in-long-term-agreement/"),
("2026-06-26","ALBAIK × AFC Asian Cup 2027","Football","Global sponsor","Global","Global sponsor of the 2027 Asian Cup in Saudi Arabia.",SM+"albaik-lands-global-sponsorship-deal-for-afc-asian-cup-saudi-arabia-2027/"),
("2026-06-11","ExpressVPN × FIFA World Cup 2026","Football","Official partner","Global","Major sponsorship of the 2026 World Cup.",MI+"11-06-2026/expressvpn-secures-major-sponsorship-2026-fifa-world-cup"),
("2026-06-10","Emirates × Real Madrid","Football","Extension","Global","Extension reported at €100m, a European record.",SP+"news/sponsorship-marketing/real-madrid-emirates-record-sponsorship-june-2026/"),
("2026-06-10","Kraken × FIFA World Cup 2026","Football","Official partner","Global","Crypto partner of the World Cup.",SP+"news/sponsorship-marketing/fifa-world-cup-2026-kraken-ab-inbev-sponsorships-june-2026/"),
("2026-06-09","Range Rover × Wimbledon","Tennis","Extension","Global","Multi-year renewal.",SM+"range-rover-drives-forward-wimbledon-alliance-with-multi-year-renewal/"),
("2026-06-08","Salesforce × FIFA World Cup","Football","Technology partner","Global","Tech partner for the 2026 and 2027 World Cups.",SM+"fifa-taps-salesforce-to-power-operations-and-fan-engagement-for-2026-and-2027-world-cups/"),
("2026-06-06","Audi × FIS","Skiing","Extension","Global","Key commercial partner through 2030.",SM+"fis-retains-key-commercial-partner-as-audi-commits-through-2030/"),
("2026-06-04","Alibaba × UEFA","Football","Technology partner","Global","AI and cloud partnership.",SM+"alibaba-powers-uefas-digital-future-in-landmark-ai-and-cloud-partnership/"),
("2026-06-04","Westfield × SBS World Cup Fan Zones","Football","Partnership","ANZ","Fan Zones for the 2026 World Cup across Australia.",MI+"04-06-2026/westfield-and-sbs-partner-fifa-world-cup-2026-fan-zones-across-australia"),
("2026-06-04","M.J. Bale × Socceroos","Football","Official supplier","ANZ","Official tailor deal renewed.",BT+"spotlight-on-sponsors-brands-tap-into-manlys-foz-ball-movement/"),
("2026-06-04","Kleenheat × Fremantle","AFL","Extension","ANZ","Expanded to the AFLW program through the end of 2027.",BT+"spotlight-on-sponsors-brands-tap-into-manlys-foz-ball-movement/"),
# ---- May
("2026-05-28","Harvey Norman × Commonwealth Games Australia","Multi-sport","Official partner","ANZ","Official partner of the team for Glasgow 2026.",BT+"spotlight-on-sponsors-harvey-norman-backs-aussie-athletes-in-commonwealth-games-gold-hunt/"),
("2026-05-28","HITIQ × Ebony Marinoff / Jamal Fogarty","Multi-sport","Athlete endorsement","ANZ","Ambassadors for the PROTEQT smart mouthguard.",BT+"spotlight-on-sponsors-harvey-norman-backs-aussie-athletes-in-commonwealth-games-gold-hunt/"),
("2026-05-27","Gucci × Alpine F1","Motorsport","Title sponsorship","Global","Title partner from 2027, reported at US$150m.",SP+"news/alpine-gucci-f1-title-partner-sponsorship-2027-renault-kering-may-2026/"),
("2026-05-27","Paula's Choice × FIFA World Cup","Football","Official partner","Global","Official skincare sponsor for the 2026 and 2027 World Cups.",MI+"27-05-2026/paulas-choice-partners-fifa-world-cup-skincare-campaign"),
("2026-05-27","Coca-Cola × Football Australia","Football","Partnership","ANZ","Major campaigns ahead of the World Cups.",MI+"27-05-2026/coca-cola-partners-football-australia-major-campaigns-ahead-world-cups"),
("2026-05-22","Paramount ANZ × APL","Football","Broadcast rights","ANZ","A-Leagues media rights extended three years.",MI+"22-05-2026/paramount-anz-and-apl-extend-media-rights-partnership-three-years"),
("2026-05-21","Afterpay × Qudos Bank Arena","Venues","Naming rights","ANZ","Sydney venue becomes Afterpay Arena for an initial five years.",BT+"spotlight-on-sponsors-hawthorn-hawks-look-to-swoop-in-on-new-front-of-guernsey-sponsor/"),
("2026-05-21","Revo Fitness × Adelaide 36ers","Basketball","Front-of-jersey","ANZ","Upgraded from shorts to front-of-jersey, to 2029.",BT+"spotlight-on-sponsors-hawthorn-hawks-look-to-swoop-in-on-new-front-of-guernsey-sponsor/"),
("2026-05-18","Polymarket × Serie A","Football","Official partner","Global","Official partner in the United States.",SM+"serie-a-brings-in-polymarket-as-official-partner-in-the-united-states/"),
("2026-05-15","Intel × McLaren Racing","Motorsport","Official partner","Global","Official compute partner.",SM+"mclaren-racing-names-intel-as-official-compute-partner/"),
("2026-05-15","Public Investment Fund × FIFA World Cup 2026","Football","Official supporter","Global","Saudi fund signs as an official supporter.",SM+"public-investment-fund-signs-on-as-official-supporter-for-fifa-world-cup-2026/"),
("2026-05-14","Deel × Arsenal","Football","Sleeve sponsorship","Global","Sleeve partner from 2026/27, replacing Visit Rwanda.",SP+"news/sponsorship-marketing/arsenal-deel-shirt-sleeve-sponsorship-visit-rwanda-may-2026/"),
("2026-05-13","Turkish Airlines × England Golf","Golf","Partnership","Global","Airline deepens its golf investment.",SM+"turkish-airlines-deepens-global-golf-investment-through-england-golf-deal/"),
("2026-05-13","Cisco × USGA","Golf","Extension","Global","Deal extended with an AI and digital focus.",SM+"cisco-extends-usga-deal-as-golf-embraces-ai-and-digital-transformation/"),
# ---- April
("2026-04-30","VoltX Energy × Manly Sea Eagles","NRL","Premier partner","ANZ","Upgraded to premier partner through at least 2028.",BT+"spotlight-on-sponsors-hours-out-from-state-of-origin-gio-goes-blue-for-the-blues/"),
("2026-04-30","Dare Iced Coffee × Melbourne Storm","NRL","Official partner","ANZ","Multi-year official partner.",BT+"spotlight-on-sponsors-hours-out-from-state-of-origin-gio-goes-blue-for-the-blues/"),
("2026-04-29","Coca-Cola × NRL","NRL","Official partner","ANZ","Three-year deal as official beverage partner of the NRL and NRLW.",MI+"29-04-2026/coca-cola-partners-nrl-three-year-sponsorship-deal"),
("2026-04-29","adidas × Bundesliga","Football","Investment","Global","€100m investment and strategic partnership with the DFL.",SP+"news/finance-investment/bundesliga-dfl-adidas-investment-strategic-partnership-april-2026/"),
("2026-04-29","CricViz × Cricket Australia","Cricket","Data partner","ANZ","Official data collection and high-performance partner.","https://www.sportcal.com/news/cricket-australia-partners-with-cricviz-ecb-lands-cawston-press-as-sponsor/"),
("2026-04-29","Cawston Press × England Cricket","Cricket","Official partner","Global","Official soft drinks and drinks break partner.","https://www.sportcal.com/news/cricket-australia-partners-with-cricviz-ecb-lands-cawston-press-as-sponsor/"),
("2026-04-23","Liquid I.V. × McLaren","Motorsport","Official partner","Global","Performance and fan engagement partnership.",SM+"mclaren-taps-liquid-i-v-to-strengthen-performance-and-fan-engagement-strategy/"),
("2026-04-22","Samsung × Canada Soccer","Football","Technology partner","Global","Tech partner ahead of the home World Cup.",SM+"canada-soccer-adds-samsung-as-key-technology-partner-ahead-of-2026-world-cup/"),
("2026-04-20","BingX × Chelsea","Football","Extension","Global","Stays as principal partner in an extended deal.",SM+"bingx-retains-principal-partner-status-at-chelsea-in-extended-agreement/"),
("2026-04-20","Y Series × NFL","NFL","Official partner","ANZ","Official wine sponsor of the NFL in ANZ.",MI+"20-04-2026/y-series-becomes-official-wine-sponsor-nfl-anz"),
("2026-04-17","XTB × FIBA","Basketball","Global partner","Global","Global partner until 2027.",SM+"fiba-secures-xtb-as-global-partner-until-2027/"),
("2026-04-16","BOSS × Australian Open","Tennis","Official supplier","ANZ","Official lifestyle outfitter from 2027.",BT+"spotlight-on-sponsors-titans-ditch-lottery-office-logo-to-raise-awareness-for-youth-cancer/"),
("2026-04-16","Chemist Warehouse × AFL","AFL","Extension","ANZ","Multi-year renewal including at least $1M over five years for umpiring.",BT+"spotlight-on-sponsors-titans-ditch-lottery-office-logo-to-raise-awareness-for-youth-cancer/"),
("2026-04-16","Capgemini × RFU","Rugby union","Technology partner","Global","Technology partner for English rugby.",SM+"capgemini-to-drive-rfus-technology-evolution-under-new-partnership/"),
("2026-04-10","Meta × Arsenal","Football","Global partner","Global","Global partnership across WhatsApp and Facebook.",SP+"news/sponsorship-marketing/arsenal-meta-facebook-whatsapp-global-partnership-april-2026/"),
("2026-04-07","Virgin Australia × Carlton","AFL","Extension","ANZ","Partnership extended three more years.",MI+"07-04-2026/virgin-australia-extends-partnership-carlton-football-club-three-more-years"),
("2026-04-07","ADI Predictstreet × FIFA World Cup","Football","Official partner","Global","Prediction market partner.",SP+"news/sponsorship-marketing/fifa-world-cup-adi-predictstreet-prediction-market-sponsorship-april-2026/"),
("2026-04-02","XFM × Perth Bears","NRL","Jersey sponsor","ANZ","Sternum sponsor for the club's first three seasons.",BT+"spotlight-on-sponsors-xfm-to-drive-the-perth-bears-for-its-first-3-seasons/"),
("2026-04-02","Carpark King × Cronulla Sharks NRLW","NRL","Shorts sponsor","ANZ","Back-of-shorts sponsor for 2026 and 2027.",BT+"spotlight-on-sponsors-xfm-to-drive-the-perth-bears-for-its-first-3-seasons/"),
("2026-04","Polymarket × Lazio","Football","Partnership","Global","Prediction market deal reported at US$22m.",SP+"sponsorship-marketing/lazio-polymarket-prediction-markets-sponsorship-serie-a-april-2026/"),
("2026-04","U.S. Bank × NFL","NFL","Official partner","Global","Official bank and wealth management sponsor.",SP+"analysis/finance-investment/nfl-2026-season-tv-rights-sponsors-valuations-finances-commercial-preview/"),
("2026-04","PayPal × NFL","NFL","Official partner","Global","Official peer-to-peer payments partner.",SP+"analysis/finance-investment/nfl-2026-season-tv-rights-sponsors-valuations-finances-commercial-preview/"),
# ---- March
("2026-03-30","Google Gemini × IPL","Cricket","Official partner","Global","AI search partnership reported at US$28.5m.",SP+"sponsorship-marketing/google-gemini-ai-ip-cricket-march-2026/"),
("2026-03-27","Wolf Lubricants × WRC","Motorsport","Extension","Global","Extended to 2029.",SP+"sponsorship-marketing/wrc-world-rally-championship-wolf-lubricants-march-2029/"),
("2026-03-26","Dreame × Sydney Swans","AFL","Partnership","ANZ","Tech brand partners with the Swans to grow in Australia.",MI+"26-03-2026/dreame-technology-partners-sydney-swans-expand-australian-market-presence"),
("2026-03-24","THE ICONIC × Newcastle Knights NRLW","NRL","Partnership","ANZ","The retailer's first sports partnership.",MI+"24-03-2026/iconic-partners-newcastle-knights-2026-nrlw-season"),
("2026-03-20","Polymarket × MLB","Baseball","Official partner","Global","Prediction market partnership.",SP+"news/betting/mlb-polymarket-predictions-market-deal-ctfc-march-2026/"),
("2026-03-19","Sprite × NBA","Basketball","Official partner","Global","Returns as the NBA's global soft drink partner.",BT+"spotlight-on-sponsors-tradies-limited-edition-sports-drink-takes-the-nrl-by-storm/"),
("2026-03-19","Sports Direct × Sydney FC","Football","Official partner","ANZ","Official sports retailer.",BT+"spotlight-on-sponsors-tradies-limited-edition-sports-drink-takes-the-nrl-by-storm/"),
("2026-03-17","Kettle Chips × ICC Women's T20 World Cup","Cricket","Official supporter","Global","Official supporter of the 2026 tournament.",SM+"kettle-chips-joins-icc-womens-t20-world-cup-2026-as-official-supporter/"),
("2026-03-14","AAMI × AFL","AFL","Extension","ANZ","Major general insurance partner for at least three more years.","https://www.ausleisure.com.au/news/afl-secures-major-partners-as-2026-premiership-season-gets-underway"),
("2026-03-14","Coles × AFL","AFL","Naming rights","ANZ","Naming rights to the Goal of the Year.","https://www.ausleisure.com.au/news/afl-secures-major-partners-as-2026-premiership-season-gets-underway"),
("2026-03-14","CyberCX × AFL","AFL","Official partner","ANZ","Official cyber security partner and AFL Review Centre naming partner.","https://www.ausleisure.com.au/news/afl-secures-major-partners-as-2026-premiership-season-gets-underway"),
("2026-03-14","TCL × AFL","AFL","Extension","ANZ","Official TV and whitegoods partner through 2028.","https://www.ausleisure.com.au/news/afl-secures-major-partners-as-2026-premiership-season-gets-underway"),
("2026-03-11","Gello Beans and Snakes × AFL","AFL","Licensing","ANZ","Five-year licensing deal.",MI+"11-03-2026/gello-beans-and-snakes-secure-afl-partnership-five-year-licensing-deal"),
("2026-03-05","Oracle × Red Bull Racing","Motorsport","Extension","Global","Title partnership extended and expanded.",BT+"spotlight-on-sponsors-brands-shift-into-gear-for-the-aussie-gp/"),
("2026-03-05","Boost Mobile × Supercars","Motorsport","Extension","ANZ","Telco partner through 2028 with an expanded role.",BT+"spotlight-on-sponsors-brands-shift-into-gear-for-the-aussie-gp/"),
("2026-03-05","City Fertility × South Sydney Rabbitohs","NRL","Official partner","ANZ","Official fertility partner.",BT+"spotlight-on-sponsors-brands-shift-into-gear-for-the-aussie-gp/"),
("2026-03-05","Brick Lane Brewing × Melbourne Storm","NRL","Partnership","ANZ","Co-branded Storm Lager.",BT+"spotlight-on-sponsors-brands-shift-into-gear-for-the-aussie-gp/"),
("2026-03-05","Carnival Cruise Line × Nine's NRL coverage","NRL","Broadcast sponsorship","ANZ","New Sunday afternoon NRL sponsor.","https://www.mediaweek.com.au/brands-pile-into-nines-nrl-as-2026-season-kicks-off"),
("2026-03-05","Jim Beam × Nine's NRL coverage","NRL","Broadcast sponsorship","ANZ","New Sunday afternoon NRL sponsor.","https://www.mediaweek.com.au/brands-pile-into-nines-nrl-as-2026-season-kicks-off"),
("2026-03","Carabao × EFL","Football","Extension","Global","League Cup title sponsorship extended to 2029.",SP+"news/sponsorship-marketing/efl-carabao-cup-sponsorship-history-march-2026/"),
# ---- February
("2026-02-26","Atlas Building × Perth Bears","NRL","Back-of-jersey","ANZ","Back-of-jersey sponsor.",BT+"spotlight-on-sponsors-brands-lace-up-for-upcoming-nrl-afl-seasons/"),
("2026-02-26","Ingenia Holiday Parks × North Queensland Cowboys","NRL","Presenting partner","ANZ","Multi-year presenting partner until October 2027.",BT+"spotlight-on-sponsors-brands-lace-up-for-upcoming-nrl-afl-seasons/"),
("2026-02-26","Revolut × Hawthorn","AFL","Official partner","ANZ","Gold partner for 2026.",BT+"spotlight-on-sponsors-brands-lace-up-for-upcoming-nrl-afl-seasons/"),
("2026-02-26","MUFG Pension & Market Services × Sydney Swans","AFL","Premier partner","ANZ","Premier partner for three seasons.",BT+"spotlight-on-sponsors-brands-lace-up-for-upcoming-nrl-afl-seasons/"),
("2026-02-26","Reebok × Jack Ginnivan","AFL","Athlete endorsement","ANZ","Multi-year deal with the Hawthorn forward.",BT+"spotlight-on-sponsors-brands-lace-up-for-upcoming-nrl-afl-seasons/"),
("2026-02-12","Blundstone × Tasmania Devils","AFL","Foundation partner","ANZ","Seven-year guernsey deal, the club's first foundation partner.",BT+"spotlight-on-sponsors-afl-flies-into-its-15th-season-with-virgin-australia/"),
("2026-02-12","Sephora × WNBL","Basketball","Foundation partner","ANZ","Foundation and official beauty partner.",BT+"spotlight-on-sponsors-afl-flies-into-its-15th-season-with-virgin-australia/"),
("2026-02-06","Vinarchy × AFL","AFL","Official partner","ANZ","Grant Burge becomes official wine partner of the AFL, AFLW and Marvel Stadium for four years.",BT+"spotlight-on-sponsors-brands-pounce-on-the-afl-ahead-of-2026-season/"),
("2026-02-06","KFC × Collingwood","AFL","Extension","ANZ","Premier partner renewed for five years.",BT+"spotlight-on-sponsors-brands-pounce-on-the-afl-ahead-of-2026-season/"),
("2026-02-06","Anthropic × Williams F1","Motorsport","Official partner","Global","Claude becomes the team's official thinking partner.",BT+"spotlight-on-sponsors-brands-pounce-on-the-afl-ahead-of-2026-season/"),
("2026-02-06","Hahn × Ripper GC","Golf","Official partner","ANZ","Official sponsor of the LIV Golf team.",BT+"spotlight-on-sponsors-brands-pounce-on-the-afl-ahead-of-2026-season/"),
("2026-02-06","Kelme × Brisbane Roar","Football","Kit supplier","ANZ","Three-year apparel partnership.",MI+"06-02-2026/brisbane-roar-secures-three-year-apparel-partnership-kelme"),
("2026-02-05","Virgin Australia × AFL","AFL","Extension","ANZ","Five more years as official airline, through 2030.","https://www.virginaustralia.com/au/en/newsroom/2026/2/virgin-australia-and-afl-kick-off-major-new-partnership/"),
("2026-02","Visa × Racing Bulls","Motorsport","Extension","Global","Title sponsorship extended in a wider Red Bull deal.",SP+"news/red-bull-racing-bulls-visa-f1-sponsorship-february-2026/"),
("2026-02","TWG AI × Cadillac F1","Motorsport","Official partner","Global","Cadillac's F1 team promotes TWG's AI technology.",SP+"news/cadillac-f1-twg-ai-sponsorship-february-2026/"),
("2026-02","IFS × Chelsea","Football","Shirt sponsorship","Global","Short-term shirt deal to the end of 2025/26.",SP+"news/sponsorship-marketing/chelsea-ifs-jersey-shirt-sponsorship-deal-february-2026/"),
# ---- January
("2026-01-28","McDonald's × Perth Bears","NRL","Major partner","ANZ","Three-year major partner, 2026 to 2028.","https://www.nrl.com/news/2026/01/28/perth-bears-and-mcdonalds-team-up-for-family-first-major-partnership/"),
("2026-01-15","ANZ × Australian Open","Tennis","Extension","ANZ","Official bank and ANZ Arena naming, a 16-year relationship.",BT+"spotlight-on-sponsors-brands-set-to-face-off-inside-rod-laver-arena/"),
("2026-01-15","a2 Milk × Australian Open","Tennis","Official partner","ANZ","Official dairy milk partner.",BT+"spotlight-on-sponsors-brands-set-to-face-off-inside-rod-laver-arena/"),
("2026-01-15","Lipton Ice Tea × Australian Open","Tennis","Official partner","ANZ","Official ice tea.",BT+"spotlight-on-sponsors-brands-set-to-face-off-inside-rod-laver-arena/"),
("2026-01-15","Jacob's Creek × Australian Open","Tennis","Official partner","ANZ","Back as official wine partner.",BT+"spotlight-on-sponsors-brands-set-to-face-off-inside-rod-laver-arena/"),
("2026-01-15","Altos × Australian Open","Tennis","Official partner","ANZ","Official tequila.",BT+"spotlight-on-sponsors-brands-set-to-face-off-inside-rod-laver-arena/"),
("2026-01-13","Nexo × Dallas Open","Tennis","Title sponsorship","Global","First-ever title partner of the ATP 500 event.",SM+"nexo-becomes-first-ever-title-partner-of-u-s-atp-500-dallas-open/"),
("2026-01-12","Tommy Hilfiger × Liverpool FC","Football","Global partner","Global","Global partnership with the club.",SM+"liverpool-fc-forge-global-partnership-with-tommy-hilfiger/"),
("2026-01-09","Marriott Bonvoy × ICC","Cricket","Official partner","Global","Travel experiences for cricket fans.",SM+"icc-and-marriott-bonvoy-join-hands-to-redefine-travel-experiences-for-global-fans/"),
("2026-01","Meta × UFC","MMA","Naming rights","Global","Naming rights to the UFC Apex venue.",SP+"news/sponsorship-marketing/ufc-meta-apex-venue-naming-rights-sponsorship-january-2026/"),
]

root = Path(__file__).resolve().parent.parent
data = json.loads((root / "deals.json").read_text(encoding="utf-8"))
norm = lambda s: "".join(sorted(p.strip().lower() for p in s.split("×")))
have = {norm(e["deal"]) for e in data["deals"]}
added, skipped = [], []
for d, deal, sport, typ, reg, summ, url in R:
    if norm(deal) in have:
        skipped.append(deal); continue
    e = {"date": d} if len(d) == 10 else {"month": d}
    e.update(deal=deal, sport=sport, type=typ, region=reg, summary=summ, url=url)
    added.append(e); have.add(norm(deal))
data["deals"].extend(added)
key = lambda e: e.get("date") or (e.get("month", "0000-00") + "-00")
data["deals"].sort(key=lambda e: (key(e), 1 if e.get("lead") else 0), reverse=True)
(root / "deals.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print("added", len(added), "skipped", skipped, "total", len(data["deals"]))
