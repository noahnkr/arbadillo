from config import Config
from scraper import *

def main():
    driver = Config.get_driver()
    leagues = ['mlb']

    # Instantiate implementations of BaseScraper
    betmgm_scraper = BetMGMScraper(driver)
    #draftkings_scraper = DraftKingsScraper(driver)
    #fanduel_scraper = FanDuelScraper(driver)
    #ceasars_scraper = CeasarsScraper(driver)
    book_scrapers = [betmgm_scraper]

    all_events = []
    for league in leagues:
        # Get a list of the events for the league from ESPN
        events = book_scrapers[0].scrape_league_events(league)
        for book in book_scrapers:
            # Append this books picks to the list of events.
            book.scrape_odds(league, events)
        
        # Once every book's picks has been added to the league's events, add these picks
        # to the final list and continue to the next league.
        all_events.extend(events)

    for event in all_events:
        print(event)
    driver.quit()
if __name__ == '__main__':
    main()
