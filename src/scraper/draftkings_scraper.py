from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re

from .base_scraper import BaseScraper
from .models import ScrapedEvent, ScrapedPick

class DraftKingsScraper(BaseScraper):
    def __init__(self, driver: WebDriver):
        super().__init__(driver, 'draftkings')

    
    def _format_event_time(date, time=None):
        if date == 'TODAY':
            event_date = datetime.today().date()
        elif date == 'TOMORROW':
            event_date = (datetime.today() + timedelta(1)).date()
        else:
            ordinal_suffix_re = re.compile(r'(\d+)(st|nd|rd|th)', re.IGNORECASE)
            cleaned_date_str = ordinal_suffix_re.sub(r'\1', date)
            event_date = datetime.strptime(cleaned_date_str, '%a %b %d').date()
            event_date = event_date.replace(year=datetime.now().year)
        if time:
            event_time = datetime.strptime(time, '%I:%M%p').time()
        else:
            event_time = datetime.min.time()
            
        return datetime.combine(event_date, event_time).isoformat()

    def _get_event_info(self, soup: BeautifulSoup):
        pass

    def scrape_odds(self, league, events):
        league_url = self._get_book_base_url(self.book_name, league)
        self.driver.get(league_url)

        try:
            tables = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'table.sportsbook-table')
                )
            )
        except Exception as e:
            print(f'{type(e).__name__} encountered while loading tables: {e}')

        scraped_events = []
        for i in range(len(tables)):
            try:
                # Re-find table elements to avoid stale element reference
                tables = self.wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, 'table.sportsbook-table')
                    )
                )
                table = tables[i]
                table_html = table.get_attribute('innerHTML')
                table_soup = BeautifulSoup(table_html, 'lxml')
                event_info = self._get_event_info(table_soup)

                event_date = table_soup.find(
                    'div', class_='sportsbook-table-header__title'
                ).text.strip()
                table_body = table_soup.find('tbody', class_='sportsbook-table__body')
                table_rows = table_body.find_all('tr')
                if len(table_rows) % 2 != 0:
                    raise ValueError('Missing event team pair.')

                team_pairs = [(table_rows[i], table_rows[i + 1]) for i in range(0, len(table_rows), 2)]
                for team_pair in team_pairs:
                    away_row, home_row = team_pair
                    event_link = away_row.find('a', class_='event-cell-link', href=True)['href']
                    event_link = f'{self.driver.current_url.split('/')[2]}/{event_link}'
                    away_team = self._get_team_abbreviation(
                            away_row.find('div', class_='event-cell__name-text').text
                        .strip()
                        .upper()
                        .split(' ')[1]
                    )
                    home_team = self._get_team_abbreviation(
                            home_row.find('div', class_='event-cell__name-text').text
                        .strip()
                        .upper()
                        .split(' ')[1]
                    )
                    try:
                        event_time = away_row.find(
                            'span', class_='event-cell__start-time'
                        ).text.strip()
                        start_time = self._format_event_time(event_date, event_time)
                        is_live = True
                    except Exception:
                        start_time = self._format_event_time(event_date)
                        is_live = False
                    
                    event = ScrapedEvent(league, away_team, home_team, start_time, is_live)
                    if event in events:
                        scraped_events.append((event_info, event_link))
            except Exception as e:
                print(f'{type(e).__name__} encountered while scraping table: {e}')
        
        for scraped_event in scraped_events:
            print(scraped_event)

    def _scrape_event(self, event_info):
        pass



    def _scrape_block(self, block: WebElement, event_info):
        pass
