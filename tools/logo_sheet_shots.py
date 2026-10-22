"""Screenshots of logo-sheet.html (every brand/club logo as the live site renders it). Used by logo-sheet.yml."""
import asyncio, os
from playwright.async_api import async_playwright
async def main():
    os.makedirs("shots", exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1400, "height": 880})
        for i in range(7):
            await pg.goto(f"https://sportsportsport.com.au/logo-sheet.html?from={i*96}&n=96&v={os.environ.get('GITHUB_RUN_ID','0')}", wait_until="domcontentloaded")
            await pg.wait_for_timeout(20000)
            await pg.screenshot(path=f"shots/sheet-{i}.png")
        await b.close()
asyncio.run(main())
