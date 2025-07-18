import asyncio
import logging
import os
from scraper import SCRAPER_CLASSES

def setup_logging(log_file="logs/scraper.log"):
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8"
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(console)

class ScraperManager:
    SCRAPER_CLASSES = SCRAPER_CLASSES

    @staticmethod
    def get_scraper(csv_path, output_csv, image_dir="images", delay=1, batch_size=5):
        for ScraperClass in ScraperManager.SCRAPER_CLASSES:
            try:
                if ScraperClass.can_handle(csv_path):
                    logging.info(f"✅ Selected {ScraperClass.__name__} for {csv_path}")
                    return ScraperClass(csv_path, output_csv, image_dir=image_dir, delay=delay, batch_size=batch_size)
            except Exception as e:
                logging.warning(f"⚠️ Error in can_handle for {ScraperClass.__name__}: {e}")
        raise ValueError(f"No scraper found that can handle: {csv_path}")

async def run_scrapers_for_all_csvs(data_dir="data/", output_dir="output/", batch_size=5):
    os.makedirs(output_dir, exist_ok=True)
    files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    if not files:
        logging.error("[ERROR] No CSV files found in the data directory!")
        return

    for fname in files:
        csv_path = os.path.join(data_dir, fname)
        output_csv = os.path.join(output_dir, fname)
        try:
            scraper = ScraperManager.get_scraper(csv_path, output_csv, batch_size=batch_size)
            await scraper.start()
            await scraper.scrape_articles()
        except Exception as e:
            logging.error(f"[ERROR] ❌ Scraping failed for {csv_path}: {e}")
        finally:
            if 'scraper' in locals():
                await scraper.stop()

if __name__ == "__main__":
    import argparse
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data/")
    parser.add_argument("--output_dir", default="output/")
    parser.add_argument("--batch_size", type=int, default=5, help="Number of articles to save in each batch")
    args = parser.parse_args()

    logging.info("🚀 Scraper Manager starting...")
    asyncio.run(run_scrapers_for_all_csvs(args.data_dir, args.output_dir, batch_size=args.batch_size))
    logging.info("✅ All scraping complete")
