from config import Config
from scraper import scrape_odds
from utils import logger
import os
import json
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Event, Sportsbook, Pick

def main():
    try:
        odds = scrape_odds(Config.LEAGUES, Config.BOOKS, Config.WEBDRIVER_THREADS)
    except Exception as e:
        logger.critical(f'Failed to scrape odds: {e}', exc_info=True)

    with open('data/export.json', 'w') as f:
        json.dump([o.to_dict() for o in odds], f, indent=4)

if __name__ == '__main__':
    main()