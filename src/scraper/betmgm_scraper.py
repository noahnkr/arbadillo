from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    StaleElementReferenceException, NoSuchElementException, TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
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
                is_live = False
                date = datetime.today().strftime('%Y-%m-%d')
                starting_mins = int(starting_soon.text.split(' ')[2]) # Very dangerous
                time = (datetime.now() + timedelta(minutes=starting_mins)).time()
                time = time.strftime('%I:%M %p')
            elif live:
                is_live = True
                date = datetime.today().strftime('%Y-%m-%d')
                time = None
            else:
                is_live = False
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
        
            return away_team, home_team, start_time, is_live
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

        event_map= {
            (event.away_team, event.home_team, event.start_time, event.is_live): event for event in events
        }

        try:
            scraped_events = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'ms-six-pack-event.grid-event')
                )
            )
        except TimeoutException:
            raise ScraperError(f'No events found for league {league} on book {self.book_name}.')

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

                soup = BeautifulSoup(event_html, 'lxml')
                event_info = self._get_event_info(soup)
                event_info = self._fuzzy_find_event(events, event_info)
                if event_info not in event_map:
                    continue

                event_link.click()
                picks = self._scrape_event(event_info)
                self._add_picks_to_matching_event(events, event_info, picks)

                self.driver.back()
                time.sleep(2)
            except StaleElementReferenceException:
                print(f'StaleElementRefernceException encountered while scraping events in {league}')
                continue
            except ScraperError as e:
                print(f'ScraperError encountered while scraping events in {league}: {type(e).__name__} - {e}')
            except Exception as e:
                print(f'Unexpected error encountered while scraping events in {league}: {type(e).__name__} - {e}')

    def _scrape_event(self, event_info):
        event_picks = []
        try:
            all_button = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'ul.event-details-pills-list li:last-child button.ds-pill')
                )
            )
            if all_button.text.strip() == 'All':
                all_button.click()
        except Exception as e:
            print(f'Error clicking all button: {e}')

        try:
            blocks = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ms-option-panel.option-panel'))
            )
        except TimeoutException as e:
            raise EventNotFoundError(f'Unable to load event blocks in event {event_info}') from e

        for block in blocks:
            try:
                event_picks.extend(self._scrape_block(block, event_info))
            except BlockNotFoundError as e:
                print(f'BlockNotFoundError in event {event_info}: {e}')
            except Exception as e:
                print(f'Unexpected error scraping block in event {event_info}: {e}')

        return event_picks

    def _scrape_block(self, block: WebElement, event_info):
        try:
            block_title = block.find_element(By.CSS_SELECTOR, 'div.header-content').text.strip()
        except NoSuchElementException:
            raise BlockNotFoundError(f'Block title could not be found.')
        

        try:
            # Expand block if it is closed
            is_closed = (
                block.find_element(By.CSS_SELECTOR, 'div.option-group-header-chevron span')
                     .get_attribute('class') == 'theme-down'
            )
            if is_closed:
                expand_button = block.find_element(By.CSS_SELECTOR, 'div.option-group-name.clickable')
                expand_button.click()
        except NoSuchElementException:
            print(f'Expand button not found in event {event_info}')
        except Exception as e:
            print(f'Error expanding block in event {event_info}: {e}')

        try:
            # If there is a show more button, click it
            show_more_button = block.find_elements(By.CSS_SELECTOR, 'div.show-more-less-button')
            if show_more_button:
                show_more_button[0].click()
        except NoSuchElementException:
            print(f'Show more button not found in event {event_info}')
        except Exception as e:
            print(f'Error clicking show more button in event {event_info}: {e}')


        try:
            # Determine block type and scrape accordingly
            block_type = (
                block.find_element(By.CSS_SELECTOR, 'div.option-group-container')
                     .get_attribute('class')
                     .split()[1]
            )
        except NoSuchElementException as e:
            raise BlockNotFoundError(f'Block type not found in event {event_info} for block {block_title}') from e

        block_html = block.get_attribute('innerHTML')
        soup = BeautifulSoup(block_html, 'lxml')

        match block_type:
            case 'six-pack-container':
                return self._scrape_six_pack_container(soup, block_title)
            case 'over-under-container':
                return self._scrape_over_under_container(soup, block_title)
            case 'player-props-container':
                return self._scrape_player_prop_container(soup, block_title)
            case _:
                raise UnsupportedBlockType(f'Unsupported block type: {block_type}')

    def _scrape_six_pack_container(self, soup: BeautifulSoup, block_title):
        game_lines = []

        rows = soup.find_all('div', class_='option-row')
        if len(rows) != 2:
            raise ValueError('Game lines must have 2 rows.')

        for row in rows:
            try:
                team_element = row.find('div', class_='six-pack-player-name')
                team = self._get_team_abbreviation(team_element.text.strip().upper())
                options = row.find_all('ms-event-pick', class_='option-pick')
                for option in options:
                    try:
                        name = option.find('div', class_='name')
                        value = option.find('div', class_='value')

                        if name and ('+' in name.text or '-' in name.text):
                            market = 'spread'
                            outcome = None
                            line = float(name.text.replace('+', ''))
                            odds = int(value.text.replace('+', ''))
                        elif name and ('O' in name.text or 'U' in name.text):
                            market = 'total'
                            outcome = 'over' if 'O' in name.text else 'under'
                            line = float(name.text.replace('O', '').replace('U', '').strip())
                            odds = int(value.text.replace('+', ''))
                        elif value:
                            market = 'moneyline'
                            outcome = None
                            line = None
                            odds = int(value.text.replace('+', ''))
                        else:
                            continue

                        game_lines.append(
                            Pick(market, team, line, odds, outcome)
                        )

                    except Exception as e:
                        print(f'Error with option in block {block_title} (game-lines): {e}')
            except Exception as e:
                print(f'Error getting team name in block {block_title} (game-lines): {e}')

        return game_lines

            
    def _scrape_over_under_container(self, soup: BeautifulSoup, block_title):
        over_unders = []

        if ':' in block_title:
            # TODO: Handle all block titles
            return []
        else:
            team = None
            market = block_title.lower().replace(' ', '_')
            if market not in MARKETS:
                print(f'Market {market} is not supported.')
                return []

        lines = soup.find_all('div', class_='attribute-key')
        options = soup.find_all('ms-option', class_='option')
        for i, option in enumerate(options):
            try:
                line = float(lines[i // 2].text)
                outcome = 'over' if i % 2 == 0 else 'under'

                option = option.find('ms-event-pick', class_='option-pick')
                if option:
                    odds = int(
                        option.find('ms-font-resizer').text
                            .replace('+', '')
                            .strip()
                    )
                    over_unders.append(
                        Pick(market, team, line, odds, outcome)
                    )
            except Exception as e:
                print(f'Error with option in block {market} (over-under): {e}')

        return over_unders

    def _scrape_player_prop_container(self, soup: BeautifulSoup, block_title):
        player_props = []

        if ':' in block_title:
            return []
        else:
            market = block_title.lower().replace(' ', '_')
            if market not in MARKETS:
                print(f'Market {market} is not supported.')
                return []

        players = soup.find_all('div', class_='player-props-player-name')
        options = soup.find_all('ms-event-pick', class_='option-pick')
        for i, option in enumerate(options):
            try:
                player = players[i // 2].text
                outcome = 'over' if i % 2 == 0 else 'under'
                line = float(
                    option.find('div', class_='name').text
                        .replace('Over', '')
                        .replace('Under', '')
                        .strip()
                )
                odds = int(
                    option.find('div', class_='value').text
                        .replace('+', '')
                        .strip()
                )
                player_props.append(
                    Pick(market, None, line, odds, outcome, player)
                )
            except Exception as e:
                print(f'Error scraping option in block {block_title} (player-prop): {e}')

        return player_props