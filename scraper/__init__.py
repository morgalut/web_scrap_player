# scraper/__init__.py
from .makorrishon_scraper import MakorRishonScraper
from .israel_hayom_scraper import IsraelHayomScraper

SCRAPER_CLASSES = [MakorRishonScraper, IsraelHayomScraper]
