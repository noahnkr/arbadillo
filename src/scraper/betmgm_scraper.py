from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    StaleElementReferenceException, NoSuchElementException, TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, PageElement
from datetime import datetime, timedelta
import time

from .base_scraper import BaseScraper
from .models import Event, Pick

from utils import MARKETS

from exceptions import (
    InputError, ScraperError, LeagueNotFoundError,
    EventNotFoundError, BlockNotFoundError,
    UnsupportedBlockType, UnsupportedBlockMarket
)

class BetMGMScraper(BaseScraper):
    def __init__(self, driver: WebDriver):
        super().__init__(driver, 'betmgm')

    def _get_event_info(self, soup: BeautifulSoup):
        try:
            event_info = soup.find('ms-event-info', class_='grid-event-info')
            starting_time = event_info.find('ms-prematch-timer', class_='starting-time')
            starting_soon = event_info.find('b')
            live = event_info.find('i')

            if starting_soon:
                active = False
                date = datetime.today().strftime('%Y-%m-%d')
                starting_mins = int(starting_soon.text.split(' ')[2]) # Very dangerous
                time = (datetime.now() + timedelta(minutes=starting_mins)).time()
                time = time.strftime('%I:%M %p')
            elif live:
                active = True
                date = datetime.today().strftime('%Y-%m-%d')
                time = None
            else:
                active = False
                time_parts = starting_time.text.split('•')
                date = time_parts[0].strip()
                time = time_parts[1].strip()

            start_time = self._format_event_time(date, time)

            participants = soup.find_all('div', class_='participant')
            if len(participants) == 2:
                away_team = self._get_team_abbreviation(participants[0].text.strip().upper())
                home_team = self._get_team_abbreviation(participants[1].text.strip().upper())
            else:
                raise ValueError('Missing participant information.')

            return away_team, home_team, start_time, active
        except AttributeError as e:
            raise ScraperError(f'Error parsing event info: {e}')

    def _format_event_time(self, date, time=None):
        if date == 'Today':
            event_date = datetime.today().date()
        elif date == 'Tomorrow':
            event_date = (datetime.today() + timedelta(1)).date()
        else:
            event_date = datetime.strptime(date, '%Y-%m-%d').date()

        if time:
            event_time = datetime.strptime(time, '%I:%M %p').time()
        else:
            event_time = datetime.min.time()

        return datetime.combine(event_date, event_time).isoformat()


    def scrape_odds(self, league, events):
        league_url = self._get_book_base_url(self.book_name, league)
        self.driver.get(league_url)

        event_map = {
            (event.away_team, event.home_team, event.start_time, event.active): event for event in events
        }

        try:
            scraped_events = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'ms-six-pack-event.grid-event')
                )
            )
        except Exception as e:
            print(f'{type(e).__name__} encountered while loading events: {e}')

        for i in range(len(scraped_events)):
            try:
                # Re-find the elements to avoid StaleElementReferenceException.
                scraped_events = self.wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, 'ms-six-pack-event.grid-event')
                    )
                )
                event_html = scraped_events[i].get_attribute('innerHTML')
                event_link = scraped_events[i].find_element(By.CSS_SELECTOR, 'a.grid-info-wrapper')
                event_soup = BeautifulSoup(event_html, 'lxml')
            except Exception as e:
                raise LeagueNotFoundError(f'Unable to load events page for league `{league}`')

            try:
                event_info = self._fuzzy_find_event(
                    self._get_event_info(event_soup), events
                )
            except Exception as e:
                print(f'{type(e).__name__} encountered while getting event info for league `{league}`: {e}')
                continue

            if event_info not in event_map:
                print(f'Event {self._event_info_to_str(event_info)} not found in list of events.')
                continue

            try:
                event_link.click()
                picks = self._scrape_event()
                self._add_picks_to_matching_event(league, event_info, events, picks)
            except Exception as e:
                print(f'{type(e).__name__} encountered while scraping event `{self._event_info_to_str(event_info)}` for league `{league}`: {e}')

            self.driver.back()
            time.sleep(2)

    def _scrape_event(self):
        event_picks = []
        try:
            # Click `All` button to show all available betting props
            all_button = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'ul.event-details-pills-list li:last-child button.ds-pill')
                )
            )
            all_button.click()
        except Exception as e:
            print(f'{type(e).__name__} encountered while clicking all button: {e}')

        try:
            blocks = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ms-option-panel.option-panel'))
            )
        except Exception as e:
            raise EventNotFoundError(f'Unable to load event blocks') from e

        # Expose all block information
        blocks_soup = []
        for block in blocks:
            try:
                # Expand block if it is closed
                is_closed = (
                    block.find_element(By.CSS_SELECTOR, 'div.option-group-header-chevron span')
                        .get_attribute('class') == 'theme-down'
                )
                if is_closed:
                    expand_button = block.find_element(By.CSS_SELECTOR, 'div.option-group-name.clickable')
                    expand_button.click()
            except Exception as e:
                print(f'{type(e).__name__} encountered while expanding block: {e}')
                
            try:
                # If there is a show more button, click it
                show_more_button = block.find_elements(By.CSS_SELECTOR, 'div.show-more-less-button')
                if show_more_button:
                    show_more_button[0].click()
            except Exception as e:
                print(f'{type(e).__name__} encountered while clicking `Show More`: {e}')
            
            block_html = block.get_attribute('innerHTML')
            block_soup = BeautifulSoup(block_html, 'lxml')
            blocks_soup.append(block_soup)

        for soup in blocks_soup:
            try:
                event_picks.extend(
                    self._scrape_block(soup)
                )
            except Exception as e:
                print(f'{type(e).__name__} encountered while scraping block: {e}')


        return event_picks

    def _scrape_block(self, soup: BeautifulSoup):
        try:
            block_title = soup.find('div', class_='header-content').get_text(strip=True)
            block_body = soup.find('div', class_='option-group-container')
            if not block_body:
                raise BlockNotFoundError(f'Missing block body in {block_title}')
            block_type = block_body['class'][1]
        except Exception as e:
            raise BlockNotFoundError(f'Unable to load block information in block {block_title}: {e}') from e

        try:
            match block_type:
                case 'six-pack-container':
                    return self._scrape_six_pack_container(block_body, block_title)
                case 'over-under-container':
                    return self._scrape_over_under_container(block_body, block_title)
                case 'player-props-container':
                    return self._scrape_player_prop_container(block_body, block_title)
                case _:
                    raise UnsupportedBlockType(f'{block_type} is not supported')
        except Exception as e:
            print(f'{type(e).__name__} encountered in block {block_type}: {e}')
            return []

    def _scrape_six_pack_container(self, block_body: PageElement, block_title):
        game_lines = []

        rows = block_body.find_all('div', class_='option-row')
        if len(rows) != 2:
            raise ValueError('Game lines must have 2 rows')

        for row in rows:
            try:
                team = self._get_team_abbreviation(
                    row.find('div', class_='six-pack-player-name')
                        .get_text(strip=True).upper()
                )
                options = row.find_all('ms-event-pick', class_='option-pick')
                for option in options:
                    name = option.find('div', class_='name')
                    value = option.find('div', class_='value')

                    if name and ('+' in name.get_text() or '-' in name.get_text()):
                        market = 'spread'
                        outcome = None
                        line = float(name.text.replace('+', ''))
                        odds = int(value.text.replace('+', ''))
                    elif name and ('O' in name.get_text() or 'U' in name.get_text()):
                        market = 'total'
                        outcome = 'over' if 'O' in name.get_text() else 'under'
                        line = float(name.get_text(strip=True).replace('O', '').replace('U', ''))
                        odds = int(value.get_text().replace('+', ''))
                    elif value:
                        market = 'moneyline'
                        outcome = None
                        line = None
                        odds = int(value.get_text().replace('+', ''))
                    else:
                        continue

                    game_lines.append(
                        Pick(market, team, line, odds, outcome)
                    )
            except Exception as e:
                print(f'{type(e).__name__} encountered while scraping option in game lines: {e}')

        return game_lines

            
    def _scrape_over_under_container(self, block_body: PageElement, block_title):
        over_unders = []
        market, team = self._get_market_name(block_title)

        options = block_body.find_all('ms-option', class_='option')
        for option in options:
            name = option.find('div', class_='name')
            value = option.find('span', class_='custom-odds-value-style')

            if name and value:
                outcome, line = name.get_text(strip=True).split(' ', 1)
                outcome = outcome.lower()
                line = float(line)
                odds = int(value.get_text(strip=True).replace('+', ''))
            else:
                continue

            over_unders.append(
                Pick(market, team, line, odds, outcome)
            )

        return over_unders

    def _scrape_player_prop_container(self, block_body: PageElement, block_title):
        player_props = []
        market, team = self._get_market_name(block_title)

        players = block_body.find_all('div', class_='player-props-player-name')
        options = block_body.find_all('ms-option', class_='option')
        for i, option in enumerate(options):
            player = players[i // 2]
            name = option.find('div', class_='name')
            value = option.find('div', class_='value')

            if player and name and value:
                player = player.get_text(strip=True)
                line = float(name.get_text(strip=True).replace('Over ', '').replace('Under ', ''))
                odds = int(value.get_text(strip=True).replace('+', ''))
                outcome = 'over' if i % 2 == 0 else 'under'
            else:
                continue

            player_props.append(
                Pick(market, team, line, odds, outcome, player)
            )

        return player_props