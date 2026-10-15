from playwright.async_api import async_playwright # ¡Importante! Versión async
import re

from app.core.logger import system_logger

async def scrape_product(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )

        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        # 🔥 Función retry asíncrona
        async def safe_goto(p, u):
            for _ in range(3):
                try:
                    await p.goto(u, wait_until="domcontentloaded", timeout=60000)
                    return True
                except Exception as e:
                    system_logger.warning(f"Reintento carga web: {e}")
                    continue
            return False

        if not await safe_goto(page, url):
            await browser.close()
            return {"title": "Error", "image": "", "description": "", "rating": None, "reviews": []}

        # --- Extracción con await ---
        title = await page.title()

        image = ""
        try:
            image = await page.locator("#landingImage").get_attribute("data-old-hires")
            if not image:
                image = await page.locator("#landingImage").get_attribute("src")
        except:
            try:
                image = await page.locator("img").first.get_attribute("src")
            except:
                pass

        description = ""
        try:
            description = await page.locator("#productDescription").inner_text()
        except:
            pass

        if not description:
            try:
                description = await page.locator("#feature-bullets").inner_text()
            except:
                pass

        rating = None
        try:
            rating_text = await page.locator("#acrPopover").get_attribute("title")
            if rating_text:
                match = re.search(r"(\d[\d,\.]*)", rating_text)
                if match:
                    rating = float(match.group(1).replace(",", "."))
        except:
            pass

        reviews = []
        try:
            reviews = await page.locator(".review-text-content span").all_text_contents()
            reviews = reviews[:5]
        except:
            reviews = ["No reviews found"]

        if description:
            description = description.strip()

        await browser.close()

        return {
            "title": title,
            "image": image,
            "description": description,
            "rating": rating,
            "reviews": reviews
        }