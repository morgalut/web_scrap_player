from .base_scraper import BaseScraper
import logging
import asyncio
import csv

class MakorRishonScraper(BaseScraper):
    SITE_NAME = "makorrishon"
    DOMAIN = "https://www.makorrishon.co.il"

    def __init__(self, csv_path, output_csv, image_dir=None, delay=1, batch_size=5):
        super().__init__()
        self.csv_path = csv_path
        self.output_csv = output_csv
        self.image_dir = image_dir
        self.delay = delay
        self.batch_size = batch_size  # <-- NEW


    def _full_url(self, link):
        link = (link or '').strip()
        if not link:
            return None
        # NEW: Ignore very short/meaningless URLs
        if link in ('/', '-', 'NA', 'N/A') or len(link) < 8:
            return None
        link = link.replace('makorrishon.co.il/makorrishon.co.il', 'makorrishon.co.il')
        if link.startswith("http://") or link.startswith("https://"):
            return link
        if link.startswith("/"):
            return f"{self.DOMAIN}{link}"
        return f"{self.DOMAIN}/{link}"


    def _detect_columns(self, first_row):
        lowered = [str(cell).strip().lower() for cell in first_row]
        if 'url' in lowered or 'link' in lowered:
            return 'header'
        if len(first_row) == 2 and (first_row[1].startswith("/") or first_row[1].startswith("http")):
            return 'id_path'
        return 'unknown'

    async def scrape_articles(self):
        with open(self.csv_path, encoding='utf-8') as infile, \
             open(self.output_csv, 'w', encoding='utf-8', newline='') as outfile:

            reader = csv.reader(infile)
            first_row = next(reader)
            fmt = self._detect_columns(first_row)

            if fmt == 'header':
                infile.seek(0)
                dict_reader = csv.DictReader(infile)
                url_fields = [k for k in dict_reader.fieldnames if k.lower() in ['url', 'link']]
                id_field = [k for k in dict_reader.fieldnames if k.lower() == 'id']
                rows_iter = dict_reader
            else:
                url_fields = [1]
                id_field = [0]
                infile.seek(0)
                rows_iter = csv.reader(infile)

            writer = csv.DictWriter(outfile, fieldnames=['id', 'url', 'title', 'subtitle', 'first_paragraph'])
            writer.writeheader()

            for row in rows_iter:
                if fmt == 'header':
                    link = None
                    _id = None
                    for f in url_fields:
                        link = row.get(f, '').strip() if row.get(f) else None
                        if link:
                            break
                    for f in id_field:
                        _id = row.get(f, '').strip() if row.get(f) else None
                elif fmt == 'id_path':
                    _id = row[0].strip()
                    link = row[1].strip()
                else:
                    logging.warning(f"⚠️ Unrecognized row format: {row}")
                    continue

                url = self._full_url(link)
                if not url:
                    logging.error(f"❌ Invalid or missing URL for row: {row}")
                    continue

                if not await self.goto(url):
                    logging.warning(f"⚠️ Failed to load {url}")
                    continue

                try:
                    # --- Robust Title Extraction ---
                    title = await self.safe_text('h1.jeg_post_title')
                    if not title:
                        title = await self.safe_text('h1.title')
                    if not title:
                        title = await self.safe_text('h1')
                    if not title:
                        title = await self.safe_text('title')

                    # --- Robust Subtitle Extraction ---
                    subtitle = await self.safe_text('h2.jeg_post_subtitle')
                    if not subtitle:
                        subtitle = await self.safe_text('span[style*="--subtitle-disable-shadow"]')
                    if not subtitle:
                        subtitle = await self.safe_text('h2')
                    if not subtitle:
                        subtitle = await self.safe_text('span[class*="subtitle"]')

                    # --- Robust First Paragraph Extraction ---
                    first_para = await self.page.evaluate('''() => {
                        let sel = s => document.querySelector(s);
                        // Try content-inner
                        let content = sel('.content-inner');
                        if (content) {
                            let p = content.querySelector('p');
                            if (p) return p.textContent.trim();
                        }
                        // Else, first <p> anywhere
                        let p = sel('p');
                        return p ? p.textContent.trim() : '';
                    }''')
                    if not first_para:
                        first_para = await self.safe_text('p')

                    writer.writerow({
                        "id": _id or '',
                        "url": url,
                        "title": (title or '').strip(),
                        "subtitle": (subtitle or '').strip(),
                        "first_paragraph": (first_para or '').strip()
                    })
                    logging.info(f"[MakorRishon] Scraped {url}")
                except Exception as ex:
                    logging.error(f"❌ Extraction failed for {url}: {ex}")
                    continue

                await asyncio.sleep(self.delay)

    @classmethod
    def can_handle(cls, csv_path):
        with open(csv_path, encoding="utf-8") as f:
            first_line = f.readline().strip().lower()
            if first_line.startswith("id,url") or first_line.startswith("id,link"):
                return True
            if "," in first_line:
                parts = first_line.split(",")
                if len(parts) == 2 and (parts[1].startswith("/") or "makorrishon" in parts[1]):
                    return True
        return False
