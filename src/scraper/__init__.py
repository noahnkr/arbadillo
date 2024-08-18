from .base_scraper import BaseScraper
from .betmgm_scraper import BetMGMScraper
from .draftkings_scraper import DraftKingsScraper

BOOK_SCRAPERS = {
    'fanduel': None, 
    'caesars': None,
    'draftkings': DraftKingsScraper,
    'betmgm': BetMGMScraper,
    'betrivers': None,
    'pointsbet': None,
    'espnbet':  None,
}

def scrape_odds(leagues, books):
    events = []

    for league in leagues:
        league_events = BaseScraper.scrape_upcoming_events(league)
        for book in books:
            BOOK_SCRAPERS[book].scrape_events(league, league_events)
        events.extend(league_events)

    return events

__all__ = [
    'scrape_odds', 'BaseScraper', 'BetMGMScraper', 'DraftKingsScraper',
]
