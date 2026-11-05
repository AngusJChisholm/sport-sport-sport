# Sport Sport Sport website

Two files run the whole site:

- `index.html` - the page design. You won't need to touch this day to day.
- `deals.json` - every deal on the site. Add a deal here and it shows up everywhere (hero, round-up, Global/ANZ columns and the archive).

## Adding a day's deals

Add new entries to the top of the `deals` list in `deals.json`:

```json
{"date":"2026-10-14","deal":"Brand × Property","sport":"AFL","type":"Official partner","region":"ANZ","lead":true,"headline":"Short punchy headline.","summary":"One line on the deal.","url":"https://link-to-source"}
```

- `date` - YYYY-MM-DD
- `region` - `Global` or `ANZ`
- `lead` - set `true` on the day's lead story only. It becomes the big hero
- `headline` - lead story only, the big display line
- `summary`, `url` - optional. With a `url`, the deal links to its source
- `month` instead of `date` (e.g. `"2026-09"`) for deals where the exact day isn't known
- No `date` or `month`, plus `"listed": "YYYY-MM-DD"`, for a current partner taken from the club's official partners page whose announcement can't be found. It shows as "Current partner" and sits at the bottom of the archive and profile pages. Swap in the real `date` once the announcement turns up

- `ended` - for a partner that's no longer signed. Use the last year of the deal (e.g. `"ended": 2026`), or `true` if the year isn't confirmed. Mark every deal for that brand and property. On brand and property pages the partner is greyed out and shows the years they were signed (e.g. "Past partner · 2021-2026"). Never delete old partners: the history stays on the site
- `tier` and `ptier` - two layers. `tier` is SSS's own deal type (one of the fixed list in `assets/data.js` TIERS), used for filters, insights, renewals and SSS Pro. `ptier` is the property's own grouping for that partner, exactly as its official partners page labels it (e.g. `"Platinum partner"`), and `ptitle` is the partner's official title if the page shows one (e.g. `"Official Airline Partner"`). Property pages group partners by `ptier`, in the order set by `ptiers` on the property in `entities.json`. Never invent a `ptier`: no groupings on the page, leave it off. Run `python3 tools/ptiers.py` before `tools/build_profiles.py`
- `since` - optional first year of a partnership, when it started before the first deal we've filed

The newest dated lead story always becomes the hero, and the other deals from that same day fill the round-up.

## Lead deal articles

Every lead deal gets its own article page in `articles/`. Add an `article` to the lead entry in `deals.json`:

```json
"article": {"standfirst": "One-sentence hook.", "body": ["Paragraph one.", "Paragraph two."], "close": "Closing line."}
```

Then run `python3 tools/build_articles.py` to generate the pages. The homepage links each lead to its article automatically.

## Features (Mon feature, Wed data drop, Fri breakdown)

Every Monday, Wednesday and Friday a scheduled task writes one piece into `features.json`: Monday a sport business feature (explainer, deep dive or trend piece), Wednesday a data drop built from our own archive, Friday a breakdown of the week's best deal. Set `"label"` to `"Feature"`, `"Data drop"` or `"Breakdown"`. Deals post Tuesday and Thursday. Nothing posts on weekends. See SOURCES.md rule 6.

```json
{"date":"2026-10-18","label":"Feature","headline":"Short punchy headline.","descriptor":"One line under the headline","topic":"Explainer","sport":"AFL","region":"ANZ","image":"https://images.unsplash.com/photo-...","related":["Brand × Property"],"article":{"standfirst":"Hook.","body":["Paragraph."],"close":"Closing line."},"sources":["https://..."]}
```

`python3 tools/build_articles.py` builds its page in `articles/` (labelled with its `label`). Features show in Key stories and the "Features" row on the homepage, but never in the deal archive. `related` lists deals already in `deals.json`; they appear under the article. Every feature has a photo, and slide 1 of its Instagram carousel (and the story) always uses the same photo as the article, pulled from `features.json`. The same task queues an Instagram carousel (`"kind": "feature"`, posts 7pm Mon/Wed, 6pm Fri) and a LinkedIn spec in `instagram/linkedin/<date>.json`.

## Logos, brand pages and club pages

Every deal shows the brand and club logos side by side in the archive. Click a logo for that brand or club's page (`profile.html?id=<slug>`): every deal they've done, who they've signed with, and a link back to the archive filtered to them. The strip above the archive (AFL, NRL, A-Leagues, NBL, BBL, Super Netball, Global clubs, Top brands) filters the archive by club or brand.

- `entities.json` holds every brand and rights holder: `name`, `domain` (official website) and optional `aliases`. New names from new deals work straight away with a monogram; add a `domain` to give them a logo.
- **Turn real logos on:** sign up free at brandfetch.com, copy the client ID from the developer dashboard and paste it into `"brandfetch": ""` at the top of `entities.json`. Brandfetch logos are loaded live on the page, as their terms require.
- **Your own logo file:** drop it in `assets/logos/` and set `"logo": "assets/logos/<file>.png"` on that entity. A local file always wins over Brandfetch.
- No logo found? A monogram shows instead, in club colours where `instagram/colours.json` has them.
- Club strips are the `leagues` list at the bottom of `entities.json`.

## Your LinkedIn link

Paste your LinkedIn page URL into `"linkedin": ""` at the top of `deals.json`. The Follow button and footer link switch on automatically.

## Hosting (GitHub Pages, free)

1. Create a GitHub repository and upload `index.html` and `deals.json`
2. In Netlify: Add new site > Import from GitHub > pick the repository. No build settings needed
3. Domain management > Add your domain, then follow Netlify's DNS steps at your registrar

Every change pushed to GitHub (including the daily update) goes live in about a minute.

## Instagram autopilot

Every weekday the afternoon Instagram task (about 1:30pm Melbourne) writes `instagram/queue/<date>.json` (the day's slides and caption), after the 6am update has posted the LinkedIn material and Angus has had the morning to confirm or swap the lead photo. The queue file uses whatever `image` the lead has in `deals.json` at that time. A GitHub Action (`.github/workflows/instagram.yml`) checks every 15 minutes, renders the images into `ig/<date>/` (served from GitHub, so none of this uses Netlify credits) and posts on this schedule, Melbourne time:

- Stories and Reels: switched off
- Carousel: Mon-Thu 7pm, Fri 6pm (Fridays are "The week in deals")
- Evergreen carousel ("The breakdown"): Tuesdays 5pm
- Stats: a daily snapshot lands in `instagram/stats/latest.json`; the Friday 6am message summarises it
- Tags and collab invites only use handles verified on official websites; if Instagram rejects one, the post goes out without it

**Stop a post:** set `"hold": true` in that day's queue file (editable in the GitHub app). **Pause everything:** add an empty file called `instagram/PAUSE`; delete it to resume.

**Carousel look (2 Nov 2026):** everything is white, centred and condensed, with no black backgrounds. Slide 1 is the lead's photo (the same one as the article and LinkedIn) fading into white, with the headline centred in the bottom third. The inner slides are white with centred numbered rows. Volt is only ever a fill behind black type (labels, sport tags, the highlighted word), never volt text on white. The LinkedIn graphics (tools/linkedin_graphics.py) keep their own layout (Angus prefers it): slide 1 is the photo with a big left-aligned stacked headline, slide 2 is the white round-up. Switches at the top of the photo section in tools/instagram_render.py: `LIGHT`, `COVER_LIGHT`, `INNER_BG`.

**Club colours** for stories live in `instagram/colours.json`. Anything not listed uses black.

**Secrets** (GitHub > Settings > Secrets and variables > Actions): `IG_USER_ID`, `IG_ACCESS_TOKEN`, and optionally `GH_PAT` (a fine-grained token with Secrets read/write on this repo) so the Instagram token renews itself every week. Without `GH_PAT` the token must be renewed by hand every 60 days.

## Partner slots (advertising)

One partner can own every slot on the site. Everything is controlled by `partners.json`:

- `active` - set to `false` to hide every slot straight away (nothing else changes)
- `name`, `url` - the partner and where clicks go. Every image, headline and link in a slot opens this site (or the slot's own `url`)
- Slots: `credit` (byline line), `feature` (split image + copy after the first paragraph), `wide` (full-width image at the end of the article), `signoff` (closing line), `presented` (in the black follow block) and `home` (between key stories and the round-up on the homepage). Delete a slot from the file to switch just that one off

Images live in `assets/partners/<partner>/`: `split.jpg` 1200×900, `wide.jpg` 1600×900, `home.jpg` 2400×800 and `home-mobile.jpg` 1600×900. Changing the partner needs no rebuild; the articles fill the slots from `partners.json` when they load. Links carry `rel="sponsored"` and UTM tags so the partner can see the traffic.

## Brands, properties and insights

Nav: News · Deals · Brands · Properties · Insights. Everything is built from `deals.json` and `entities.json`; nothing needs updating by hand day to day.

- **Data on each deal** (added by `tools/enrich.py`, from the deal's own type and summary only): `tier` (Naming rights, Title sponsor, Principal & major, Kit & apparel, Shirt & kit placement, Official partner, Media & broadcast, Licensing & merchandise, Ambassador & endorsement, Investment & ownership), `status` (New, Renewal, Extension, Expansion), `term` (years, only when stated), `ends` (year, stated or worked out from the term, with `endsEst: true` when worked out) and `value` (only when a value is reported). Anything the deal doesn't say is left out. Fix a wrong one by editing it in `deals.json`; it won't be overwritten (add `"tierLock": true` to keep a hand-set tier).
- **Data on each organisation** (`entities.json`): `cat` = industry category for brands, `ptype` = Club & team, National team, League & competition, Event, Governing body, Athlete & talent, Venue or Other for properties, `k` = b/p (set by the build). New brand names get a category automatically where the name makes it clear; set `cat` by hand for the rest. Merge duplicate names by adding the other name to `aliases`.
- **Pages:** `brands.html`, `properties.html` (directories), `insights.html` (charts), `categories.html` (and `?c=<category>`), `renewals.html` (renewal watch), `leagues.html` (club × category maps), `compare.html` (`?a=<slug>&b=<slug>`), `news.html` (every article).
- **A page for every brand and property:** `brands/<slug>.html` and `properties/<slug>.html`, plus `sitemap.xml`, built by `tools/build_profiles.py` so Google can index them. The `profiles.yml` GitHub Action runs `enrich.py` and `build_profiles.py` every time `deals.json` changes, so the 6am update keeps them current.
