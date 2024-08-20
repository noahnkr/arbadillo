from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, PageElement
from datetime import datetime, timedelta
from config import Config
import time

from .base_scraper import BaseScraper
from .models import ScrapedEvent, ScrapedPick

from utils import (
    logger,
    ScraperError, LeagueNotFoundError,
    EventNotFoundError, BlockNotFoundError,
    UnsupportedBlockType,
)

class BetMGMScraper(BaseScraper):

    def __init__(self):
        # TODO: Handle different states
        super().__init__('betmgm', 'https://sports.il.betmgm.com')

    @staticmethod
    def _get_event_info(soup: BeautifulSoup, league):
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

            start_time = BetMGMScraper._format_event_time(date, time)

            participants = soup.find_all('div', class_='participant')
            if len(participants) == 2:
                away_team = BetMGMScraper._get_team_abbreviation(league, participants[0].text.strip().upper())
                home_team = BetMGMScraper._get_team_abbreviation(league, participants[1].text.strip().upper())
            else:
                logger.error(f'Missing participant information. Expected: 2, Actual: {len(participants)}')
                raise ValueError('Missing participant information.')

            return away_team, home_team, start_time, active
        except AttributeError as e:
            logger.error(f'Error parsing event info: {e}')
            raise ScraperError(f'Error parsing event info: {e}')

    @staticmethod
    def _format_event_time(date, time=None):
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

        return datetime.combine(event_date, event_time)

    def scrape_event_urls(self, league, events, driver: WebDriver):
        driver.get(self._get_book_base_url(league))
        self._scroll_to_bottom(driver)
        time.sleep(2)

        try:
            event_elements = self._locate_element_with_retries(
                driver, By.CSS_SELECTOR, 'ms-six-pack-event.grid-event', multiple=True, refresh=True
            )
        except Exception as e:
            logger.error(f'{type(e).__name__} encountered while loading events: {e}')
            raise LeagueNotFoundError(f'{type(e).__name__} encountered while loading events: {e}')
        
        event_urls = []
        for event_element in event_elements:
            try:
                event_html = event_element.get_attribute('innerHTML')
                event_soup = BeautifulSoup(event_html, 'lxml')
                event_url = f'{self.book_domain}{event_soup.select_one('a.grid-info-wrapper')['href']}'
                event_info = self._get_event_info(event_soup, league)
                scraped_event = ScrapedEvent(
                    league, event_info[0], event_info[1], event_info[2], event_info[3]
                )
                if scraped_event in events:
                    event_urls.append((scraped_event, event_url))
            except Exception as e:
                logger.error(f'{type(e).__name__} encountered while getting event info for league `{league}`: {e}')
        
        return event_urls

    def scrape_event_page(self, league, event, url, driver: WebDriver):
        driver.get(url)
        try:
            # Click `All` button to show all available betting props
            all_button = self._locate_element_with_retries(
                driver, By.CSS_SELECTOR, 'ul.event-details-pills-list li:last-child button.ds-pill'
            )
            all_button.click()
        except Exception as e:
            logger.error(f'{type(e).__name__} encountered while clicking all button in event `{event}`: {e}')

        try:
            # Wait for blocks to load
            blocks = self._locate_element_with_retries(
                driver, By.CSS_SELECTOR, 'ms-option-panel.option-panel', multiple=True, refresh=True, explicit_wait=2
            )
        except Exception as e:
            logger.error(f'Unable to load event blocks in event `{event}')
            raise EventNotFoundError(f'Unable to load event blocks in event `{event}') from e

        block_soup = []
        for block in blocks:
            try:
                # If the market name is not supported, continue to the next block
                block_title = block.find_element(By.CSS_SELECTOR, 'span.market-name').text.strip()
                self._normalize_market_name(block_title)
            except Exception as e:
                logger.error(f'{type(e).__name__} encountered while getting block title: {e}')
                continue

            try:
                # If the block is closed, expand it
                is_closed = (
                    block.find_element(By.CSS_SELECTOR, 'div.option-group-header-chevron span')
                        .get_attribute('class') == 'theme-down'
                )
                if is_closed:
                    expand_button = block.find_element(By.CSS_SELECTOR, 'div.option-group-name.clickable')
                    expand_button.click()
            except Exception as e:
                logger.error(f'{type(e).__name__} encountered while expanding block in event `{event}`: {e}')
                
            try:
                # If there is a show more button, click it to expose more picks
                show_more_button = driver.find_elements(By.CSS_SELECTOR, 'div.show-more-less-button')
                if show_more_button:
                    show_more_button[0].click()
            except Exception as e:
                logger.error(f'{type(e).__name__} encountered while clicking `Show More` in `{event}`: {e}')

            # Save block HTML info
            block_soup.append(BeautifulSoup(
                block.get_attribute('innerHTML'), 'lxml'
                )
            )

        # Scrape each block
        event_picks = []
        for soup in block_soup:
            try:
                block_type = soup.select_one('div.option-group-container')['class'][1]
                logger.info(f'Scraping block `{block_type}`')
                match block_type:
                    case 'six-pack-container':
                        event_picks.extend(self._scrape_six_pack_container(soup, league))
                    case 'over-under-container':
                        event_picks.extend(self._scrape_over_under_container(soup))
                    case 'player-props-container':
                        event_picks.extend(self._scrape_player_prop_container(soup))
                    case 'regular-option-container':
                        event_picks.extend(self._scrape_regular_option_container(soup, league))
                    case 'spread-container':
                        event_picks.extend(self._scrape_spread_container(soup, league))
                    case _:
                        raise UnsupportedBlockType(f'{block_type} is not supported')
            except Exception as e:
                logger.error(f'{type(e).__name__} encountered while scraping `{block_type}` in `{event}`: {e}')

        return event_picks

    def _scrape_six_pack_container(self, soup: BeautifulSoup, league):
        game_lines = []

        rows = soup.find_all('div', class_='option-row')
        if len(rows) != 2:
            raise ValueError('Game lines must have 2 rows')

        for row in rows:
            team = self._get_team_abbreviation(
                league,
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
                    ScrapedPick(market, team, line, odds, outcome)
                )
        return game_lines

    def _scrape_over_under_container(self, soup: BeautifulSoup):
        over_unders = []
        block_title = soup.select_one('span.market-name').get_text(strip=True)
        market, team = self._normalize_market_name(block_title)

        options = soup.find_all('ms-option', class_='option')
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
                ScrapedPick(market, team, line, odds, outcome)
            )

        return over_unders

    def _scrape_player_prop_container(self, soup: BeautifulSoup):
        player_props = []
        block_title = soup.select_one('span.market-name').get_text(strip=True)
        market, team = self._normalize_market_name(block_title)

        players = soup.find_all('div', class_='player-props-player-name')
        options = soup.find_all('ms-option', class_='option')
        for i, option in enumerate(options):
            player = players[i // 2]
            name = option.find('div', class_='name')
            value = option.find('div', class_='value')

            if player and name and value:
                player = player.get_text(strip=True)
                line = float(
                    name.get_text(strip=True)
                        .replace('Over ', '')
                        .replace('Under ', ''))
                odds = int(
                    value.get_text(strip=True)
                        .replace('+', '')
                )
                outcome = 'over' if i % 2 == 0 else 'under'
            else:
                continue

            player_props.append(
                ScrapedPick(market, team, line, odds, outcome, player)
            )

        return player_props

    def _scrape_regular_option_container(self, soup: BeautifulSoup):
        options = []
        block_title = soup.select_one('span.market-name').get_text(strip=True)
        market, team = self._normalize_market_name(block_title)

        outcomes = soup.select('div.name')
        odds = soup.select('div.value')

        for outcome, odd in zip(outcomes, odds):
            outcome = outcome.get_text(strip=True).lower()
            odd = int(odd.get_text(strip=True).replace('+', ''))
            options.append(ScrapedPick(market, team, None, odd, outcome))

        return options

    def _scrape_spread_container(self, soup: BeautifulSoup, league):
        spreads = []
        block_title = soup.select_one('span.market-name').get_text(strip=True)
        market, _ = self._normalize_market_name(block_title)

        participants = soup.select('div.option-group-header span')
        options = soup.select('div.option-indicator')

        for i, option in enumerate(options):
            team = self._get_team_abbreviation(
                league,
                participants[i % 2].get_text(strip=True).upper()
            )
            line = float(
                option.select_one('div.name').get_text(strip=True)
                    .replace('+', '')
            )
            odds = int(
                option.select_one('div.value').get_text(strip=True)
                    .replace('+', '')
            )
            spreads.append(ScrapedPick(market, team, line, odds))

        return spreads