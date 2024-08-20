from config import Config
from scraper import scrape_odds
import os
import json
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Event, Sportsbook, Pick

def main():
    start_time = time.time()
    odds = scrape_odds(Config.LEAGUES, Config.BOOKS, Config.WEBDRIVER_THREADS)
    print(f'Execution Time: {time.time() - start_time}s')

    with open('data/export.json', 'w') as f:
        json.dump([o.to_dict() for o in odds], f, indent=4)

if __name__ == '__main__':
    main()
