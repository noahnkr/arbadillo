from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    StaleElementReferenceException, NoSuchElementException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import hashlib
import time

from .base_scraper import BaseScraper
from .exceptions import (
    InputError, ScraperError, LeagueNotFoundError,
    EventNotFoundError, BlockNotFoundError,
)
from .utils import LEAGUES, TEAM_ACRONYMS, BOOK_BASE_URL

class BetMGMScraper(BaseScraper):
    def __init__(self, driver: WebDriver):
        super().__init__(driver, 'betmgm')

    def _get_event_info(self, soup: BeautifulSoup) -> tuple:
        participants = soup.find_all('div', class_='participant-name')
        if len(participants) < 2:
            raise ValueError('Not enough participant information found')

        participant1 = self._get_team_abbreviation(
            participants[0].text.strip().upper()
        )
        participant2 = self._get_team_abbreviation(
            participants[1].text.strip().upper()
        )

        date_element = soup.find('span', class_='date')
        time_element = soup.find('span', class_='time')

        if date_element and time_element:
            date = date_element.text.strip()
            time = time_element.text.strip()
            try:
                datetime_ = self._format_event_datetime(date, time)
            except Exception as e:
                print(f'Error formatting event datetime: {type(e).__name__} - {e}')
                date = datetime.today().strftime('%Y-%m-%d')
                datetime_ = f'{date}_LIVE'
        else:
            date = datetime.today().strftime('%Y-%m-%d')
            datetime_ = f'{date}_LIVE'

        return participant1, participant2, datetime_


    def _format_event_datetime(self, date: str, time: str) -> str:
        if date.lower() == 'today':
            date = datetime.now().date()
        elif date.lower() == 'tomorrow':
            date = (datetime.now() + timedelta(1)).date()
        else:
            date = datetime.strptime(date, '%m/%d/%y').date()
        
        time = datetime.strptime(time, '%I:%M %p').time()
        formatted_datetime = datetime.combine(date, time)
        return formatted_datetime.strftime('%Y-%m-%d_%H:%M')


    def _scrape_league(self, league: str) -> list:
        league_picks = []
        league_url = self._get_base_url(league)
        self.driver.get(league_url)

        try:
            # Wait for main content to load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'main'))
            )

        except Exception as e:
            raise LeagueNotFoundError(f'Error loading league page for {league}') from e

        try:
            # Wait for each clickable event to load
            events = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'a.grid-info-wrapper')
                )
            )
            exepected_length = len(events)
            for i in range(exepected_length):
                try:
                    max_retries = 3
                    for _ in range(max_retries):
                        # Re-find the event element to avoid stale element reference
                        events = self.wait.until(
                            EC.presence_of_all_elements_located(
                                (By.CSS_SELECTOR, 'a.grid-info-wrapper')
                            )
                        )
                        if len(events) != exepected_length:
                            print('Not all events loaded. Waiting...')
                            time.sleep(3)
                        else:
                            break

                    event = events[i]
                    event.click()
                    league_picks.extend(
                        self._scrape_event(league)
                    )
                    self.driver.back()
                except ScraperError as e:
                    print(f'Error scraping event in {league}: {type(e).__name__} - {e}')
                except Exception as e:
                    print(f'Unexpected error in league {league}: {type(e).__name__} - {e}')

        except Exception as e:
            print(f'Error loading events in {league}: {type(e).__name__} - {e}')

        return league_picks


    def _scrape_event(self, league: str) -> list:
        event_picks = []
        try:
            # Wait for game header to load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.main-score-container'))
            )

            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            away, home, datetime_ = self._get_event_info(soup)
            event = f'{away}@{home}_{datetime_}'

            print(f'Scraping event: {event}')

            blocks = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ms-option-panel.option-panel'))
            )
        except Exception as e:
            raise EventNotFoundError(f"Error loading event page for league {league}") from e


        for block in blocks:
            try:
                event_picks.extend(
                    self._scrape_block(block, league, event)
                )
            except BlockNotFoundError as e:
                print(f'Error scraping block in event {event}: {type(e).__name__} - {e}')
            except Exception as e:
                print(f'Unexpected error in event {event}: {type(e).__name__} - {e}')
        
        return event_picks


    def _scrape_block(self, block: WebElement, league: str, event: str) -> list:
        block_picks = []
        # Expand block if it is closed
        try:
            is_closed = (
                block.find_element(By.CSS_SELECTOR, 'div.option-group-header-chevron span')
                     .get_attribute('class') == 'theme-down'
            )
            if is_closed:
                expand_button = block.find_element(By.CSS_SELECTOR, 'div.option-group-name.clickable')
                expand_button.click()
        except NoSuchElementException:
            print(f'Expand button not found in event {event}')
        except Exception as e:
            print(f'Error expanding block in event {event}: {type(e).__name__} - {e}')

        # If there is a show more button, click it
        try:
            show_more_button = block.find_elements(By.CSS_SELECTOR, 'div.show-more-less-button')
            if show_more_button:
                show_more_button[0].click()
        except NoSuchElementException:
            print(f'Show more button not found in event {event}')
        except Exception as e:
            print(f'Error clicking show more button in event {event}: {type(e).__name__} - {e}')

        try:
            block_title = block.find_element(By.CSS_SELECTOR, 'div.header-content').text.upper()
        except NoSuchElementException as e:
            raise BlockNotFoundError(f'Block title not found in event {event}')
        except Exception as e:
            raise BlockNotFoundError(f'Error getting block title in event {event}') from e

        try:
            block_type = (
                block.find_element(By.CSS_SELECTOR, 'div.option-group-container')
                     .get_attribute('class')
                     .split()[1]
            )
        except NoSuchElementException as e:
            raise BlockNotFoundError(f'Block type not found in event {event} for block {block_title}')
        except Exception as e:
            raise BlockNotFoundError(f'Error getting block type in event {event} for block {block_title}') from e

        block_html = block.get_attribute('innerHTML')
        soup = BeautifulSoup(block_html, 'lxml')

        match block_type:
            case 'six-pack-container':
                block_picks.extend(
                    self._scrape_game_line_container(soup, league, event, block_title)
                )
            case 'over-under-container':
                block_picks.extend(
                    self._scrape_over_under_container(soup, league, event, block_title)
                )
            case 'player-props-container':
                block_picks.extend(
                    self._scrape_player_prop_container(soup, league, event, block_title)
                )
            case _:
                raise ValueError(f'Unsupported Block type: {block_type}')

        return block_picks


    def _scrape_game_line_container(
            self, soup: BeautifulSoup, league: str,
            event: str, block_title: str) -> list:
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
                            pick_type = 'SPREAD'
                            line = float(name.text.replace('+', ''))
                            odds = int(value.text.replace('+', ''))
                        elif name and ('O' in name.text or 'U' in name.text):
                            pick_type = 'OVER' if 'O' in name.text else 'UNDER'
                            line = float(name.text.replace('O', '').replace('U', '').strip())
                            odds = int(value.text.replace('+', ''))
                        elif value:
                            pick_type = 'MONEYLINE'
                            line = None
                            odds = int(value.text.replace('+', ''))
                        else:
                            # Pick is locked
                            continue
                        pick = self._create_pick(event, self.book_name, league, pick_type,
                                                 team, line, odds, None, None)
                        game_lines.append(pick)

                    except Exception as e:
                        print(f'Error with option in block {block_title} (game-lines): {type(e).__name__} - {e}')
            except Exception as e:
                print(f'Error getting team name in block {block_title} (game-lines): {type(e).__name__} - {e}')

        return game_lines

            
    def _scrape_over_under_container(
            self, soup: BeautifulSoup, league: str,
            event: str, block_title: str) -> list:
        over_unders = []

        if ':' in block_title:
            title_parts = block_title.split(':')
            team = self._get_team_abbreviation(title_parts[0].strip())
            pick_title = title_parts[1].strip().replace(' ', '-')
        else:
            team = None
            pick_title = block_title.strip().replace(' ', '-')

        lines = soup.find_all('div', class_='attribute-key')
        options = soup.find_all('ms-option', class_='option')
        for i, option in enumerate(options):
            try:
                line = float(lines[i // 2].text)
                pick_type = f'{pick_title}_{'OVER' if i % 2 == 0 else 'UNDER'}'

                option = option.find('ms-event-pick', class_='option-pick')
                if option:
                    odds = int(
                        option.find('ms-font-resizer').text
                            .replace('+', '')
                            .strip()
                    )
                    pick = self._create_pick(event, self.book_name, league, pick_type,
                                                team, line, odds, None, None)
                    over_unders.append(pick)
            except Exception as e:
                print(f'Error with option in block {pick_type} (over-under): {type(e).__name__} - {e}')

        return over_unders


    def _scrape_player_prop_container(
            self, soup: BeautifulSoup, league: str, 
            event: str, block_title: str) -> list:
        player_props = []

        players = soup.find_all('div', class_='player-props-player-name')
        options = soup.find_all('ms-event-pick', class_='option-pick')
        pick_type = 'PLAYER-PROP'
        for i, option in enumerate(options):
            try:
                player = players[i // 2].text
                prop = f'{block_title.replace(' ', '-')}_{'OVER' if i % 2 == 0 else 'UNDER'}'
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
                pick = self._create_pick(event, self.book_name, league, pick_type,
                                         None, line, odds, player, prop)
                player_props.append(pick)
            except Exception as e:
                print(f'Error with option in block {block_title} (player-prop): {type(e).__name__} - {e}')
    
        return player_props