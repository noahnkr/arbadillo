from .base_scraper import BaseScraper
from .betmgm_scraper import BetMGMScraper
from .draftkings_scraper import DraftKingsScraper
from concurrent.futures import ThreadPoolExecutor
from config import Config
from utils import logger
import time

def get_book_scraper(book_name) -> BaseScraper:
    BOOK_SCRAPERS = {
        'fanduel': None, 
        'caesars': None,
        'draftkings': DraftKingsScraper,
        'betmgm': BetMGMScraper,
        'betrivers': None,
        'pointsbet': None,
        'espnbet':  None,
    }
    return BOOK_SCRAPERS.get(book_name)

def scrape_odds(leagues, books, threads):
    events = []
    # WebDriver at index 0 is used to scrape the upcoming schedule
    book_drivers = [Config.get_driver() for _ in range(threads)]

    start_time = time.time()
    for league in leagues:
        logger.info(f'Scraping league `{league}`')
        league_events = BaseScraper.scrape_scheduled_events(league, book_drivers[0])
        for book in books:
            logger.info(f'Scraping book `{book}`')
            book_scraper = get_book_scraper(book)()
            event_urls = book_scraper.scrape_event_urls(league, league_events, book_drivers[0])
            # Evenly distribute event URLs to each driver
            avg, remainder = divmod(len(event_urls), threads)
            event_url_slices = [
                event_urls[i * avg + min(i, remainder):(i + 1) * avg + min(i + 1, remainder)] for i in range(threads)
            ]
            for i, s in enumerate(event_url_slices):
                u = [f'- {t[1]}' for t in s]
                logger.info(f'Driver {i + 1} Queue:\n{'\n'.join(u)}')

            with ThreadPoolExecutor(threads) as thread:
                try:
                    results = thread.map(book_scraper.scrape_events, league, event_url_slices, book_drivers)
                    for result in results:
                        for event, picks in result:
                            book_scraper._add_picks_to_matching_event(event, league_events, picks)
                except Exception as e:
                    logger.critical(f'{type(e).__name__} encountered while scraping event pool')
        events.extend(league_events)
    
    logger.info(f'Execution Time: {time.time() - start_time}s')
    
    logger.info('Quitting...')
    for bd in book_drivers:
        bd.quit()
    
    return events

__all__ = [
    'scrape_odds', 'BaseScraper', 'BetMGMScraper', 'DraftKingsScraper',
]
