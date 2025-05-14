import logging
from playwright.async_api import async_playwright

class BaseScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.page = None

    async def start(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        logging.info("🧭 Browser session started")

    async def stop(self):
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
        except:
            return None

    async def safe_attr(self, selector, attr, timeout=3000):
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return await self.page.get_attribute(selector, attr)
        except:
            return None
