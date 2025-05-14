import os
import pandas as pd
import logging
import asyncio
from scraper.base_scraper import BaseScraper
from scraper.utils import append_row_to_csv

class IsraelHayomScraper(BaseScraper):
    def __init__(self, csv_path, output_csv, image_dir="images", delay=2):
        super().__init__(headless=True)
        self.base_url = "https://www.israelhayom.co.il"
        self.csv_path = csv_path
        self.output_csv = output_csv
        self.image_dir = image_dir
        self.delay = delay

        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs(os.path.dirname(self.output_csv), exist_ok=True)

        self.visited_urls = set()
        if os.path.exists(self.output_csv):
            try:
                df_existing = pd.read_csv(self.output_csv)
                if 'Landing Page' in df_existing.columns:
                    self.visited_urls = set(df_existing['Landing Page'].dropna().astype(str).str.strip().tolist())
                    logging.info(f"🔁 Loaded {len(self.visited_urls)} previously scraped URLs.")
            except Exception as e:
                logging.warning(f"⚠️ Could not load existing output CSV: {e}")

    async def scrape_single_row(self, row, index, total):
        raw_url = row.get("Landing Page") or row.get("Url")
        if pd.isna(raw_url) or not isinstance(raw_url, str) or raw_url.strip() == "":
            logging.error(f"❌ Invalid or missing URL for row {index+1}, skipping...")
            return

        url = raw_url.strip()
        if url in self.visited_urls:
            logging.info(f"⏩ Already scraped: {url}")
            return

        page = await self.browser.new_page()
        try:
            logging.info(f"🌐 [{index+1}/{total}] Opening {url}...")
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")

            title = row.get("title", "")
            subtitle = row.get("subtitle", "")
            date_published = row.get("date_published", "")
            date_updated = row.get("date_updated", "")

            needs_title = not isinstance(title, str) or title.strip() == ""
            needs_subtitle = not isinstance(subtitle, str) or subtitle.strip() == ""
            needs_date = not isinstance(date_published, str) or date_published.strip() == ""
            needs_update = not isinstance(date_updated, str) or date_updated.strip() == ""

            if needs_title:
                try:
                    h1 = page.locator("h1")
                    if await h1.count() > 0:
                        title = (await h1.nth(0).text_content() or "").strip()
                        logging.info(f"🟢 Title (h1): {title}")
                    else:
                        title = await page.title()
                        logging.info(f"🟡 Title (<title>): {title}")
                except Exception as e:
                    logging.warning(f"⚠️ Title extraction failed for {url}: {e}")

            if needs_subtitle:
                try:
                    subtitle_el = page.locator("h2.single-post-subtitle span.titleText")
                    if await subtitle_el.count() > 0:
                        subtitle = (await subtitle_el.nth(0).text_content() or "").strip()
                        logging.info(f"🟢 Subtitle (primary): {subtitle}")
                    else:
                        span_fallback = page.locator("span.titleText")
                        if await span_fallback.count() > 0:
                            subtitle = (await span_fallback.nth(0).text_content() or "").strip()
                            logging.info(f"🟡 Subtitle (fallback): {subtitle}")
                except Exception as e:
                    logging.warning(f"⚠️ Subtitle extraction failed for {url}: {e}")

            if needs_date or needs_update:
                try:
                    times = page.locator("span.single-post-meta-dates time")
                    count = await times.count()
                    if count > 0:
                        if needs_date:
                            date_published = await times.nth(0).get_attribute("datetime") or date_published
                        if count > 1 and needs_update:
                            date_updated = await times.nth(1).get_attribute("datetime") or date_updated
                except Exception as e:
                    logging.warning(f"⚠️ Date extraction failed for {url}: {e}")

            await asyncio.sleep(self.delay)

            output_row = [
                url,
                row.get("Impressions", ""),
                row.get("Url Clicks", ""),
                row.get("URL CTR", ""),
                title,
                subtitle,
                date_published,
                date_updated,
            ]
            append_row_to_csv(self.output_csv, output_row)
            logging.info(f"💾 Saved row for URL: {url}")
            self.visited_urls.add(url)

        except Exception as e:
            logging.error(f"❌ Failed to scrape {url}: {e}")
        finally:
            await page.close()

    async def scrape_articles(self):
        df = pd.read_csv(self.csv_path)
        total = len(df)

        if not os.path.exists(self.output_csv):
            with open(self.output_csv, "w", newline="", encoding="utf-8-sig") as f:
                pd.DataFrame(columns=[
                    "Landing Page", "Impressions", "Url Clicks", "URL CTR",
                    "title", "subtitle", "date_published", "date_updated"
                ]).to_csv(f, index=False)

        BATCH_SIZE = 10
        for i in range(0, total, BATCH_SIZE):
            batch = df.iloc[i:i + BATCH_SIZE]
            tasks = [
                self.scrape_single_row(row, index=i + j, total=total)
                for j, row in enumerate(batch.to_dict(orient="records"))
            ]
            await asyncio.gather(*tasks)
