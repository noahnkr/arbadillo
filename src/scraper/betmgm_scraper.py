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

from ..exceptions import (
    InputError, ScraperError, LeagueNotFoundError,
    EventNotFoundError, BlockNotFoundError,
    UnsupportedBlockType
)

class BetMGMScraper(BaseScraper):
    def __init__(self, driver: WebDriver):
        super().__init__(driver, 'betmgm')

    def _get_event_info(self, soup: BeautifulSoup):
        try:
            event_info = soup.find('ms-event-info', class_='grid-event-info')
            starting_time = event_info.find('ms-prematch-timer', class_='starting-time')

            if starting_time:
                active = False
                time_parts = starting_time.text.split('•')
                date = time_parts[0].strip()
                time = time[1].strip()
            else:
                active = True
                date = datetime.today().strftime('%Y-%m-%d')
                time = None

            event_time = self._format_event_time(date, time)

            participants = event_info.find_all('div', class_='participant')
            if len(participants) == 2:
                away_team = self._get_team_abbreviation(participants[0].text.strip())
                home_team = self._get_team_abbreviation(participants[1].text.strip())
            else:
                raise ValueError('Missing participant information.')
        
            return away_team, home_team, event_time, active
        except AttributeError as e:
            raise ScraperError(f'Error parsing event info: {e}')

    def _format_event_time(date, time=None):
        if date == 'Today':
            event_time = datetime.today().date()
        elif date == 'Tomorrow':
            event_time = (datetime.today() + timedelta(1)).date()
        else:
            event_time = datetime.strptime(date, '%m/%d/%y').date()

        if time:
            time = datetime.strptime(time, '%I:%M %p').time()
            event_time = datetime.combine(event_time, time)

        return event_time.isoformat()

    def scrape_odds(self, league, events):
        league_url = self._get_book_base_url(self.book_name, league)
        self.driver.get(league_url)

        expected_length = len(events)
        for i in range(expected_length):
            try:
                # Wait for all events to load.
                scraped_events = self._load_events_with_retries(
                    (By.CSS_SELECTOR, 'ms-six-pack-event.grid-event'), len(events)
                )
                event_html = scraped_events[i].get_attribute('innerHTML')
                event_link = scraped_events[i].find_element(By.CSS_SELECTOR, 'a.grid-info-wrapper')

                soup = BeautifulSoup(event_html, 'lxml')
                event_info = self._get_event_info(soup)

                event_link.click()
                picks = self._scrape_event(event_info)
                self._add_picks_to_matching_event(events, event_info[0], event_info[1], event_info[2], picks)
                self.driver.back()
            except ScraperError as e:
                print(f'ScraperError while scraping events in {league}: {type(e).__name__} - {e}')
            except Exception as e:
                print(f'Unexpected error while scraping events in {league}: {type(e).__name__} - {e}')

    def _scrape_event(self, event_info):
        event_picks = []
        try:
            # Wait for game header to load
            blocks = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ms-option-panel.option-panel'))
            )
        except TimeoutException as e:
            raise EventNotFoundError(f'Unable to load event blocks in event {event_info[0]}@{event_info[1]}_{event_info[2]}') from e

        for block in blocks:
            try:
                event_picks.extend(self._scrape_block(block, event_info))
            except BlockNotFoundError as e:
                print(f'BlockNotFoundError in event {event_info[0]}@{event_info[1]}_{event_info[2]}: {e}')
            except Exception as e:
                print(f'Unexpected error scraping block in event {event_info[0]}@{event_info[1]}_{event_info[2]}: {e}')

        return {
            'book_name': self.book_name,
            'last_update': datetime.now().isoformat(),
            'picks': [p.to_dict() for p in event_picks]
        }

    def _scrape_block(self, block: WebElement, event_info):
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
            # Get the block title
            block_title = block.find_element(By.CSS_SELECTOR, 'div.header-content').text.upper()
        except NoSuchElementException as e:
            raise BlockNotFoundError(f'Block title not found in event {event_info}') from e

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
            title_parts = block_title.split(':')
            team = self._get_team_abbreviation(title_parts[0].strip())
            market = title_parts[1].strip().replace(' ', '-')
        else:
            team = None
            market = block_title.strip().replace(' ', '-')

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

        players = soup.find_all('div', class_='player-props-player-name')
        options = soup.find_all('ms-event-pick', class_='option-pick')
        for i, option in enumerate(options):
            try:
                player = players[i // 2].text
                prop = f'{block_title.replace(" ", "-")}_{"OVER" if i % 2 == 0 else "UNDER"}'
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
                    Pick(None, None, line, odds, None, player, prop)
                )
            except Exception as e:
                print(f'Error scraping option in block {block_title} (player-prop): {e}')

        return player_props