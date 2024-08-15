from config import Config
from scraper import BaseScraper
from utils import get_book_scraper

def main():
    driver = Config.get_driver()

    all_events = []
    for league in Config.LEAGUES:
        league_events = BaseScraper.scrape_league_events(driver, league)
        for book in Config.BOOKS:
            scraper = get_book_scraper(book, driver)
            scraper.scrape_odds(league, league_events)
        all_events.extend(league_events)
        
    driver.quit()

if __name__ == '__main__':
    main()
