import asyncio
import logging
import os
from scraper.israel_hayom_scraper import IsraelHayomScraper

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

async def run_scraper():
    scraper = IsraelHayomScraper(
        csv_path="data/Weather.csv",
        output_csv="output/Weather.csv",
        image_dir="images",
        delay=2
    )
    # צריך לתקן את שתי הקבצי ה CSV של NEWS ו-SPORT לפרק אותם לשתי קבצים כל אחד ולהריץ אותם שוב 

    await scraper.start()
    try:
        await scraper.scrape_articles()
    except Exception as e:
        logging.error(f"❌ Unexpected error during scraping: {e}")
    finally:
        await scraper.stop()

if __name__ == "__main__":
    setup_logging()
    logging.info("🚀 Starting Israel Hayom Scraper")
    asyncio.run(run_scraper())
    logging.info("✅ Scraping complete")
