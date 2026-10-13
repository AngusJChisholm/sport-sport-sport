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

The newest dated lead story always becomes the hero, and the other deals from that same day fill the round-up.

## Lead deal articles

Every lead deal gets its own article page in `articles/`. Add an `article` to the lead entry in `deals.json`:

```json
"article": {"standfirst": "One-sentence hook.", "body": ["Paragraph one.", "Paragraph two."], "close": "Closing line."}
```

Then run `python3 tools/build_articles.py` to generate the pages. The homepage links each lead to its article automatically.

## Your LinkedIn link

Paste your LinkedIn page URL into `"linkedin": ""` at the top of `deals.json`. The Follow button and footer link switch on automatically.

## Hosting (GitHub Pages, free)

1. Create a GitHub repository and upload `index.html` and `deals.json`
2. In Netlify: Add new site > Import from GitHub > pick the repository. No build settings needed
3. Domain management > Add your domain, then follow Netlify's DNS steps at your registrar

Every change pushed to GitHub (including the daily update) goes live in about a minute.

## Instagram autopilot

Every weekday the 6am update writes `instagram/queue/<date>.json` (the day's slides, stories and caption). A GitHub Action (`.github/workflows/instagram.yml`) checks every 15 minutes, renders the images into `ig/<date>/` (served from GitHub, so none of this uses Netlify credits) and posts on this schedule, Melbourne time:

- Stories: 8am every weekday
- Carousel: Mon 7pm, Tue 7pm, Wed 12pm, Thu 9am, Fri 6pm (Fridays are "The week in deals")
- Reel (animated version of the carousel, shown in the Reels tab): Mon/Tue 8:30pm, Wed/Thu 7pm, Fri 8pm
- Evergreen carousel ("The breakdown"): Tuesdays 12pm
- Stats: a daily snapshot lands in `instagram/stats/latest.json`; the Friday 6am message summarises it
- Tags and collab invites only use handles verified on official websites; if Instagram rejects one, the post goes out without it

**Stop a post:** set `"hold": true` in that day's queue file (editable in the GitHub app). **Pause everything:** add an empty file called `instagram/PAUSE`; delete it to resume.

**Club colours** for stories live in `instagram/colours.json`. Anything not listed uses black.

**Secrets** (GitHub > Settings > Secrets and variables > Actions): `IG_USER_ID`, `IG_ACCESS_TOKEN`, and optionally `GH_PAT` (a fine-grained token with Secrets read/write on this repo) so the Instagram token renews itself every week. Without `GH_PAT` the token must be renewed by hand every 60 days.
