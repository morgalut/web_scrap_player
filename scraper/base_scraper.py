import logging
import asyncio
from playwright.async_api import async_playwright

class BaseScraper:
    def __init__(self, headless=True, batch_size=5, delay=1):
        self.headless = headless
        self.batch_size = batch_size
        self.delay = delay
        self.browser = None
        self.page = None
        self.articles = []

    async def start(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        logging.info("🧭 Browser session started")

    async def stop(self):
        await self.page.close()
        await self.browser.close()
        await self.pw.stop()
        logging.info("🛑 Browser session closed")

    async def goto(self, url, timeout=15000):
        try:
            await self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            return True
        except Exception as e:
            logging.error(f"❌ Failed navigation: {url} | Reason: {e}")
            return False

    async def safe_text(self, selector, timeout=3000):
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return await self.page.text_content(selector)
        except Exception:
            return None

    async def safe_attr(self, selector, attr, timeout=3000):
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return await self.page.get_attribute(selector, attr)
        except Exception:
            return None

    def load_articles(self, csv_path):
        """
        Override in subclass: Load articles/URLs from CSV.
        """
        raise NotImplementedError

    async def scrape_article(self, article):
        """
        Override in subclass: Scrape a single article. Must be async.
        """
        raise NotImplementedError

    async def scrape_articles_in_batches(self, articles):
        """
        Scrapes articles in parallel batches (default batch_size=5).
        """
        total = len(articles)
        for i in range(0, total, self.batch_size):
            batch = articles[i:i+self.batch_size]
            # Each article can have its own page for full concurrency if needed
            await asyncio.gather(*(self.scrape_article_wrapper(article) for article in batch))
            await asyncio.sleep(self.delay)

    async def scrape_article_wrapper(self, article):
        """
        Opens a new page for each article (so Playwright can handle true concurrency).
        Closes the page after scraping.
        """
        page = await self.browser.new_page()
        try:
            return await self.scrape_article(article, page=page)
        finally:
            await page.close()

    async def scrape_articles(self):
        """
        Main entry: loads articles and scrapes them in batches.
        Subclass should call this after start().
        """
        if not self.articles:
            raise ValueError("No articles loaded for scraping.")
        await self.scrape_articles_in_batches(self.articles)
