from .base_scraper import BaseScraper
from .betmgm_scraper import BetMGMScraper
from .draftkings_scraper import DraftKingsScraper
from concurrent.futures import ThreadPoolExecutor
from config import Config

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

def scrape_odds(leagues, books):
    events = []
    # WebDriver at index 0 is used to scrape the upcoming schedule
    book_drivers = [Config.get_driver() for _ in range(Config.WEBDRIVER_THREADS)]

    for league in leagues:
        league_events = BaseScraper.scrape_scheduled_events(league, book_drivers[0])
        for book in books:
            book_scraper = get_book_scraper(book)()
            event_urls = book_scraper.scrape_event_urls(league, league_events, book_drivers[0])
            avg = len(event_urls) / float(Config.WEBDRIVER_THREADS)
            event_url_slices = [event_urls[int(i * avg): int((i + 1) * avg)] for i in range(Config.WEBDRIVER_THREADS)]
            with ThreadPoolExecutor(Config.WEBDRIVER_THREADS) as thread:
                results = thread.map(book_scraper.scrape_events, event_url_slices, book_drivers)
                for result in results:
                    for event, picks in result:
                        book_scraper._add_picks_to_matching_event(event, league_events, picks)
        events.extend(league_events)
    
    print('quitting...')
    for bd in book_drivers:
        bd.quit()

    return events

__all__ = [
    'scrape_odds', 'BaseScraper', 'BetMGMScraper', 'DraftKingsScraper',
]
