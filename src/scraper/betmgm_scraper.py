from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, PageElement
from datetime import datetime, timedelta
from config import Config
import time
from concurrent.futures import ThreadPoolExecutor

from .base_scraper import BaseScraper
from .models import ScrapedEvent, ScrapedPick

from utils import (
    ScraperError, LeagueNotFoundError,
    EventNotFoundError, BlockNotFoundError,
    UnsupportedBlockType,
)

class BetMGMScraper(BaseScraper):

    @staticmethod
    def _get_event_info(soup: BeautifulSoup):
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
                away_team = BetMGMScraper._get_team_abbreviation(participants[0].text.strip().upper())
                home_team = BetMGMScraper._get_team_abbreviation(participants[1].text.strip().upper())
            else:
                raise ValueError('Missing participant information.')

            return away_team, home_team, start_time, active
        except AttributeError as e:
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

        return datetime.combine(event_date, event_time).isoformat()

    @staticmethod
    def scrape_events(league, events):
        # Initialize a single WebDriver to scrape the initial list of events
        driver = Config.get_driver()
        driver.get(BetMGMScraper._get_book_base_url('betmgm', league))

        try:
            scraped_events = WebDriverWait(driver, Config.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'ms-six-pack-event.grid-event')
                )
            )
        except Exception as e:
            driver.quit()
            raise LeagueNotFoundError(f'{type(e).__name__} encountered while loading events: {e}')
        
        # Get a list of the links to the event pages
        event_links = []
        for event in scraped_events:
            try:
                event_html = event.get_attribute('innerHTML')
                event_link = event.find_element(By.CSS_SELECTOR, 'a.grid-info-wrapper').get_attribute('href')
                event_soup = BeautifulSoup(event_html, 'lxml')
                event_info = BetMGMScraper._fuzzy_find_event(
                    BetMGMScraper._get_event_info(event_soup), events
                )
                scraped_event = ScrapedEvent(
                    league, event_info[0], event_info[1], event_info[2], event_info[3]
                )

            except Exception as e:
                print(f'{type(e).__name__} encountered while getting event info for league `{league}`: {e}')
                continue

            if scraped_event in events:
                event_links.append((scraped_event, event_link))

        driver.quit()

        drivers = [Config.get_driver() for _ in range(Config.WEBDRIVER_THREADS)]
        with ThreadPoolExecutor(Config.WEBDRIVER_THREADS) as executor:
            for i, (event, link) in enumerate(event_links):
                executor.submit(BetMGMScraper._scrape_event_thread, event, link, events, drivers[i % Config.WEBDRIVER_THREADS])

        for d in drivers:
            d.quit()

    @staticmethod
    def _scrape_event_thread(event, link, events, driver):
        try:
            event_picks = BetMGMScraper.scrape_event_page(link, event, driver)
            BetMGMScraper._add_picks_to_matching_event(
                event, 'betmgm', events, event_picks
            )
        except Exception as e:
            print(f'{type(e).__name__} encountered while scraping event `{event}`: {e}')

    @staticmethod
    def scrape_event_page(event_url, event, driver=None):
        event_picks = []
        if driver is None:
            driver = Config.get_driver()
        driver.get(event_url)

        # Wait for event blocks to load
        WebDriverWait(driver, Config.WEBDRIVER_WAIT_TIME).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div.event-detail-wrapper')
            )
        )

        try:
            # Click `All` button to show all available betting props
            all_button = WebDriverWait(driver, Config.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'ul.event-details-pills-list li:last-child button.ds-pill')
                )
            )
            all_button.click()
        except Exception as e:
            print(f'{type(e).__name__} encountered while clicking all button in event `{event}`: {e}')

        try:
            # Locate each block
            blocks = WebDriverWait(driver, Config.WEBDRIVER_WAIT_TIME).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'ms-option-panel.option-panel')
                )
            )
        except Exception as e:
            raise EventNotFoundError(f'Unable to load event blocks in event `{event}') from e

        blocks_soup = []
        for block in blocks:
            # Expose all block information
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
                print(f'{type(e).__name__} encountered while expanding block in event `{event}`: {e}')
                
            try:
                # If there is a show more button, click it to expose more picks
                show_more_button = block.find_elements(By.CSS_SELECTOR, 'div.show-more-less-button')
                if show_more_button:
                    show_more_button[0].click()
            except Exception as e:
                print(f'{type(e).__name__} encountered while clicking `Show More` in `{event}`: {e}')

            # Save block HTML info
            blocks_soup.append(
                BeautifulSoup(
                    block.get_attribute('innerHTML'),
                    'lxml'
                )   
            )

        # Scrape each block
        for soup in blocks_soup:
            try:
                event_picks.extend(
                    BetMGMScraper._scrape_block_picks(soup)
                )
            except Exception as e:
                print(f'{type(e).__name__} encountered while scraping block in `{event}`: {e}')

        return event_picks

    def _scrape_block_picks(soup: BeautifulSoup):
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
                    return BetMGMScraper._scrape_six_pack_container(block_body, block_title)
                case 'over-under-container':
                    return BetMGMScraper._scrape_over_under_container(block_body, block_title)
                case 'player-props-container':
                    return BetMGMScraper._scrape_player_prop_container(block_body, block_title)
                case _:
                    raise UnsupportedBlockType(f'{block_type} is not supported')
        except Exception as e:
            print(f'{type(e).__name__} encountered in block {block_type}: {e}')
            return []

    @staticmethod
    def _scrape_six_pack_container(block_body: PageElement, block_title):
        game_lines = []

        rows = block_body.find_all('div', class_='option-row')
        if len(rows) != 2:
            raise ValueError('Game lines must have 2 rows')

        for row in rows:
            try:
                team = BetMGMScraper._get_team_abbreviation(
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
            except Exception as e:
                print(f'{type(e).__name__} encountered while scraping option in game lines: {e}')

        return game_lines

    @staticmethod
    def _scrape_over_under_container(block_body: PageElement, block_title):
        over_unders = []
        market, team = BetMGMScraper._get_market_name(block_title)

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
                ScrapedPick(market, team, line, odds, outcome)
            )

        return over_unders

    @staticmethod
    def _scrape_player_prop_container(block_body: PageElement, block_title):
        player_props = []
        market, team = BetMGMScraper._get_market_name(block_title)

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
                ScrapedPick(market, team, line, odds, outcome, player)
            )

        return player_props