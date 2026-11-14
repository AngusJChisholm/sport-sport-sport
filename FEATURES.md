# Feature days playbook (Mon feature, Wed data drop, Fri breakdown)

The scheduled tasks for Monday, Wednesday and Friday follow this file. Each run makes ONE piece and publishes it to
the website, LinkedIn (post copy plus 2 graphics) and Instagram (one carousel). Deals post Tuesday and Thursday from
the deals task. Nothing posts on weekends. Work through every step without waiting for input.

## Standing rules

**No approval prompts.** Angus is not there to approve anything. Only WebFetch a URL written out in full in the task
prompt or this file, or one that came back in a WebSearch or WebFetch result in this run. Never type, guess or build
a URL (no editing paths, no query strings, no URLs from memory). To reach any page, WebSearch first and fetch from the
results. If a fetch is refused or asks for approval, skip it and use another source. Never use a browser or
computer-use tool. Give any subagent this same rule.

**Voice.** Plain, punchy, Australian spelling and vernacular, confident. No em dashes (use hyphens or restructure),
no "it's not X, it's Y" constructions, no corporate or AI-sounding phrasing, no closing question. Brand first in every
pairing ("Turkish Airlines × Liverpool FC"; plain "x" in Instagram and LinkedIn graphic text). Never promise a posting
cadence ("daily", "every weekday"). Say "partnership(s)", never "deal(s)", and "database", never "archive", in everything people read (site, posts, captions, graphics, articles, snippets, summaries). A quote copied word for word from a source stays as it is. File names, JSON keys (deals.json, "deal") and commit messages don't change.

**Accuracy beats everything.** Official sources first (league, club and brand newsrooms, annual reports, filings),
then reputable outlets (SportsPro, SportBusiness, Sportcal, The Athletic, AFR, The Australian, SMH/The Age, B&T,
Mumbrella, mi-3, Reuters, Bloomberg). Never use Scout or any paid database as a source. Figures, lengths and
"record/first" claims need an official source or two independent reputable outlets, otherwise leave them out. Never
say who a brand replaced unless an official release says so. Write in your own words, never copying sentences.

## Steps

1. **Repo.** Attach AngusJChisholm/sport-sport-sport with push access (add_repo), then
   `git clone --depth 1 https://github.com/AngusJChisholm/sport-sport-sport` (or `git pull`). Read README.md,
   SOURCES.md (rules 5 and 6 especially), features.json (every piece so far: never repeat a topic), and the top 60
   entries of deals.json. Never change CNAME, netlify.toml or _redirects.

2. **Pick and research** per the day's brief (below). 10-20 web searches in parallel batches for Monday and Friday;
   Wednesday is mostly computed from our own data, with searches only to check it.

3. **Accuracy gate (mandatory).** Write a fact sheet: every factual claim (names, roles, dates, figures, lengths,
   counts, rankings, first/record claims) with its source URL or, for data drops, the exact query you ran on our JSON.
   Launch one independent verification subagent (Agent tool, model "sonnet") with only the fact sheet and the no
   approval rule. It re-opens each source (or re-runs each query) and marks every claim PASS or FAIL: right parties
   and roles, dates right, figures sourced, signed not "in talks", still current. Remove or rewrite anything that
   fails. Every claim in the article, LinkedIn and Instagram text must map to a PASS line.

4. **Article.** Add to the TOP of "features" in features.json:
   `{"date":"YYYY-MM-DD" (today, Melbourne), "label":"Feature | Data drop | Breakdown", "headline":"3-7 words, ends with a full stop", "descriptor":"one plain line, max ~60 characters", "topic":"Explainer | Deep dive | Trend | ANZ spotlight | Analysis | Data | Breakdown", "sport":"main sport or Multi-sport", "region":"ANZ or Global", "image":"see step 5", "related":["Brand × Property", ...], "article":{"standfirst":"one-sentence hook","body":["paragraph", ...],"close":"one closing line"}, "sources":["url", ...]}`
   `related`: up to 6 deals that exist in deals.json exactly as their "deal" field. Run
   `python3 tools/build_articles.py`, then validate features.json with `python3 -c "import json;json.load(open('features.json'))"`.

5. **Photo (required).** One free Unsplash photo used everywhere (article, LinkedIn slide 1, Instagram slide 1).
   In order of preference: the brand central to the story (product, logo, shop, livery); a real professional game or
   event in the right sport with play or a crowd; the right venue with a crowd. Never generic stock (ball on grass,
   empty pitch, lone hoop, boots, posed training, park games, skylines), never the wrong code, never another club's
   stadium or kit when the story is about one club, no rival brand front and centre, no close-ups of identifiable
   athletes, no photo already used in deals.json or features.json. How: WebSearch with allowed_domains
   ["unsplash.com"], fetch only unsplash.com URLs from the results, and only use free photos whose URL starts
   https://images.unsplash.com/photo- (never plus.unsplash.com, Unsplash+ or /flagged/). Store the base URL only, with
   "imageCredit":"Unsplash". Up to 8 searches; only if none passes, publish without and tell Angus plainly.

6. **LinkedIn (post copy + 2 graphics).**
   - Write instagram/linkedin/<date>.json:
     `{"date":"YYYY-MM-DD","headline_lines":["3-5 short lines","of the headline","in caps-friendly words"],"highlight":"one line from headline_lines to colour volt","deal":"line 1 under the headline (e.g. Brand x Property, or the subject)","descriptor":"line 2 (e.g. Feature, Data drop, Breakdown)","label":"slide 2 heading","others":[{"deal":"2-5 word bold line","sub":"one short line"}, ... 3 to 5 rows],"image":"the features.json image"}`
     Slide 2 heading by day: Monday "The key points", Wednesday "The numbers", Friday "The partnership". The "image" must equal
     the features.json "image".
   - Post copy, ready to paste: a hook line, 3-4 short paragraphs with the best of the piece, one line on why it
     matters for brands and rights holders, then "Full story in the comments." Under 1,300 characters. No hashtags
     except the four at the end: #sportsbusiness #sponsorship #sportsmarketing #partnerships. Put @ in front of each
     brand and property name the first time it appears so Angus can tag them himself (don't look up page URLs).

7. **Instagram.** Write instagram/queue/<date>.json:
   `{"date":"YYYY-MM-DD","hold":false,"feed":{"kind":"feature","cover":{"tag":"<label>","region":"ANZ or Global","headline":"3-7 words, ends with a full stop","highlight":"one word from it","deal":"the descriptor, short","descriptor":"the topic"},"slides":[{"label":"2-3 words","title":"3-7 word line","rows":[{"main":"2-5 words","sub":"one short line"}, ... 2 or 3]}, ... 3 slides, max 4]},"caption":"Hook line, 3-4 short sentences, 'Read the full story: link in bio', then exactly: #sportsbusiness #sponsorship #sportsmarketing #partnerships. Under 2,000 characters.","tags":[{"username":"official_handle","slide":1}],"collaborators":["official_handle"]}`
   Slide 1 pulls the photo from features.json automatically. Tags (max 2, slide 1) and one collaborator (an Australian
   or NZ club, league or team only) only with a handle you found today on that organisation's own official site or
   release; otherwise omit the keys. Never write "stories", "reel_caption", "story_time" or "evergreen". If the queue
   file already exists or instagram/PAUSE exists, don't write it and say so. Validate the JSON.
   Posts automatically Mon/Wed 7pm, Fri 6pm (Melbourne).

8. **Publish.** Commit features.json, the article page, the LinkedIn spec and the queue file as Angus:
   `git -c user.name="Angus Chisholm" -c user.email="AngusJChisholm@users.noreply.github.com" commit -m "<Label> for <date>"`,
   `git fetch origin main`, rebase if needed, push to main. Then wait for the GitHub-rendered LinkedIn graphics: `git pull`
   every 30 seconds for up to 8 minutes (Monitor tool or a background loop, not a foreground sleep) until
   ig/<date>/linkedin/sss-<date>-slide1.png and -slide2.png exist. Look at both. If they never arrive, render locally
   with tools/linkedin_graphics.py (slide 1 may be plain black without the photo) and say so. If the piece can't pass
   the accuracy gate, publish nothing and say why.

9. **Send Angus** (SendUserMessage + SendUserFile), short, same voice:
   - The LinkedIn post copy, ready to paste.
   - The two LinkedIn graphics.
   - The article link for the first comment: https://sportsportsport.com.au/articles/<slug> (no .html - the site uses clean URLs)
   - One line on the photo (what it shows, brand / sport / venue) so he can ask for a swap.
   - Accuracy line: "Accuracy check: X claims checked, Y passed, Z cut and why", plus a one-line source list.
   - One line: Instagram carousel queued for 7pm (Friday 6pm), tags or collab used, and that "hold": true in
     instagram/queue/<date>.json stops it.
   - If anything failed, say plainly what.

## Day briefs

**Monday - Feature** (label "Feature"). One sport business feature: an explainer, deep dive, trend piece or ANZ
spotlight on sponsorship, media rights, naming rights, ownership and investment, venues, league economics, athlete
commercial deals, betting and alcohol rules, women's sport growth, or fan and membership business. Lean on what moved
last week, but it should stay useful for months. Alternate ANZ-led and global week to week (ANZ when in doubt). 600-900
words, 5-8 paragraphs.

**Wednesday - Data drop** (label "Data drop", topic "Data"). One insight built from our own data: deals.json,
coverage.json and the properties pages. Examples: "Every NRL club's betting partner",
"Which categories signed the most ANZ deals this year", "How many AFL clubs have an airline partner", "Renewals vs new
deals in 2026". Compute every number with Python on the JSON (show the query on the fact sheet), and only use data
sets that are complete enough to be fair: for a "every club" piece, every club in scope must be in coverage.json with a
recent lastChecked, otherwise pick another angle or narrow it. Spot-check the 3 most important data points against the
official partners page or release. Say what the data covers ("from the SSS database, X partnerships logged since ...").
350-550 words, 4-6 paragraphs. The Instagram slides and LinkedIn slide 2 carry the numbers.

**Friday - Breakdown** (label "Breakdown", topic "Breakdown"). Pick the best deal logged this week (Tuesday and
Thursday runs, "added" this week in deals.json). Unpack it: what the deal is, length and value if verified, what the
brand is buying and why, what the property gets, how it fits the brand's wider sport portfolio and the category, and
what to watch next. Re-research it properly (official release first), don't just restate the Tuesday or Thursday
article. Put the deal in "related". 500-750 words. Also read instagram/stats/latest.json and add a short "Instagram this
week" section to the message: followers and 7-day change, posts, best post with link, likes, comments, saves, shares,
reach where available, and one plain-English suggestion. If "insights_available" is false or the file is stale, say so
in one line.
