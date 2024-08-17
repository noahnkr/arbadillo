from config import Config
from scraper import BaseScraper
from utils import get_book_scraper
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Event, Sportsbook, Pick

def main():
    driver = Config.get_driver()

    all_events = []
    for league in Config.LEAGUES:
        league_events = BaseScraper.scrape_league_events(driver, league)
        for book in Config.BOOKS:
            scraper = get_book_scraper(book, driver)
            scraper.scrape_odds(league, league_events)
        all_events.extend(league_events)
    
    for scraped_event in all_events:
        event, created = Event.objects.get_or_create(
            league=scraped_event.league,
            away_team=scraped_event.away_team,
            home_team=scraped_event.home_team,
            start_time=scraped_event.start_time,
            active=scraped_event.active,
        )
        for scraped_sportsbook in scraped_event.books:
            sportsbook = Sportsbook.objects.create(
                event=event,
                title=scraped_sportsbook['title'],
                last_update=scraped_sportsbook['last_update'],
            )
            for scraped_pick in scraped_sportsbook['picks']:
                Pick.objects.create(
                    sportsbook=sportsbook,
                    market=scraped_pick,
                    team=scraped_pick.team,
                    line=scraped_pick.line,
                    odds=scraped_pick.odds,
                    player=scraped_pick.player,
                    outcome=scraped_pick.outcome,
                )
        
    driver.quit()

if __name__ == '__main__':
    main()
