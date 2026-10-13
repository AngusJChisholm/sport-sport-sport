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

## Your LinkedIn link

Paste your LinkedIn page URL into `"linkedin": ""` at the top of `deals.json`. The Follow button and footer link switch on automatically.

## Going live (Netlify, free)

1. Create a GitHub repository and upload `index.html` and `deals.json`
2. In Netlify: Add new site > Import from GitHub > pick the repository. No build settings needed
3. Domain management > Add your domain, then follow Netlify's DNS steps at your registrar

Every change pushed to GitHub (including the daily update) goes live in about a minute.
