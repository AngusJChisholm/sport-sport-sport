"""Pull post lists (date, link, title, short excerpt) from WordPress news sites for the archive backfill.
Usage: wp_fetch.py <site> <after YYYY-MM-DD> <before YYYY-MM-DD> [search]. Writes wp-report.json."""
import json, sys, time, urllib.request, urllib.parse, re, html
site, after, before = sys.argv[1], sys.argv[2], sys.argv[3]
search = sys.argv[4] if len(sys.argv) > 4 else ""
out, page = [], 1
while page <= 40:
    q = {"after": after + "T00:00:00", "before": before + "T23:59:59", "per_page": 100, "page": page,
         "_fields": "date,link,title,excerpt"}
    if search: q["search"] = search
    url = f"https://{site}/wp-json/wp/v2/posts?" + urllib.parse.urlencode(q)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (SSS archive bot)"})
        data = json.load(urllib.request.urlopen(req, timeout=30))
    except Exception as e:
        out.append({"error": str(e), "url": url}); break
    if not data: break
    for p in data:
        ex = re.sub(r"<[^>]+>", "", html.unescape(p.get("excerpt", {}).get("rendered", ""))).strip()[:220]
        out.append({"d": p["date"][:10], "t": html.unescape(p["title"]["rendered"]), "u": p["link"], "x": ex})
    if len(data) < 100: break
    page += 1; time.sleep(1.5)
json.dump(out, open("wp-report.json", "w"), ensure_ascii=False, indent=0)
print(len(out), "posts")
