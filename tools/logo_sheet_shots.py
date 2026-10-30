"""Screenshots of logo-sheet.html: every brand/property logo as the site renders it (missing ones tinted red).
Used by logo-sheet.yml. Serves the checked-out branch locally, so it shows the branch, not the live site."""
import asyncio, os, json, subprocess, time
from playwright.async_api import async_playwright
N = 96
async def main():
    os.makedirs("shots", exist_ok=True)
    srv = subprocess.Popen(["python3", "-m", "http.server", "8000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(2)
    total = sum(1 for v in json.load(open("entities.json"))["entities"].values() if v.get("k"))
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1600, "height": 1000})
        # Brandfetch only serves logos to the site's own address, so present the live site as the referrer.
        async def ref(route):
            h = dict(route.request.headers); h["referer"] = "https://sportsportsport.com.au/"
            await route.continue_(headers=h)
        await pg.route("**/*brandfetch.io/**", ref)
        # The new pages as a visitor sees them, scrolled through so every logo gets requested.
        PAGES = [("page-home", "index.html", 1440, "#active"), ("page-brands", "brands.html", 1440, None),
                 ("page-properties-afl", "properties.html?league=AFL", 1440, None), ("page-collingwood", "properties/collingwood.html", 1440, None),
                 ("page-league-map", "leagues.html", 1440, None), ("page-insights", "insights.html", 1440, None),
                 ("page-renewals", "renewals.html?year=2027", 1440, None), ("page-news", "news.html", 1440, None),
                 ("page-compare", "compare.html?a=adidas&b=nike", 1440, None), ("page-brands-mobile", "brands.html", 390, None)]
        for name, url, w, anchor in PAGES:
            await pg.set_viewport_size({"width": w, "height": 1000 if w > 500 else 844})
            await pg.goto(f"http://localhost:8000/{url}", wait_until="domcontentloaded")
            await pg.wait_for_timeout(3000)
            for y in range(0, 6000, 700):
                await pg.evaluate(f"window.scrollTo(0,{y})"); await pg.wait_for_timeout(1200)
            await pg.evaluate("window.scrollTo(0,0)" if not anchor else f"document.querySelector('{anchor}').scrollIntoView()")
            await pg.wait_for_timeout(8000)
            await pg.screenshot(path=f"shots/{name}.png", full_page=True)
        await pg.set_viewport_size({"width": 1600, "height": 1000})
        for i in range((total + N - 1) // N):
            await pg.goto(f"http://localhost:8000/logo-sheet.html?from={i*N}&n={N}", wait_until="domcontentloaded")
            await pg.wait_for_timeout(35000)
            await pg.screenshot(path=f"shots/sheet-{i:02d}.png", full_page=True)
        await b.close()
    srv.terminate()
asyncio.run(main())
