from abc import ABC, abstractmethod
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
import time
from utils import logger

from .models import ScrapedEvent, ScrapedBook, ScrapedPick

from utils import LEAGUES, TEAM_ACRONYMS, SCHEDULE_BASE_URL, BOOK_BASE_URL, MARKET_MAPPINGS

class BaseScraper(ABC):

    def __init__(self, book_name, book_domain):
        self.book_name = book_name
        self.book_domain = book_domain

    def scrape_events(self, league, event_urls, driver: WebDriver) -> tuple[ScrapedEvent, list[ScrapedPick]]:
        event_picks = []
        for event, url in event_urls:
            try:
                logger.info(f'Scraping event `{event}`')
                picks = self.scrape_event_page(league, event, url, driver)
                event_picks.append((event, picks))
            except Exception as e:
                logger.error(f'{type(e).__name__} encountered while scraping `{event} in `{self.book_name}`: {e}')
        return event_picks

    @abstractmethod
    def scrape_event_urls(self, league, events, driver):
        pass

    @abstractmethod
    def scrape_event_page(self, event, url, driver) -> list[ScrapedPick]:
        '''
        Scrapes an event page for a certain sportsbook.

        This function scrapes all available game and player prop odds for this event,
        and stores the data in a list.

        Paramters:
            event (ScrapedEvent): The event information.
            url (str): The url of the event page on this sportsbook.

        Returns:
            list[ScrapedPick]: 
           
        '''
        pass

    @staticmethod
    def scrape_scheduled_events(league, driver):
        '''
        Scrapes the list of upcoming and live events for the specified league from the schedule page.

        This method navigates to the schedule page for the given league, parses the page to extract 
        event information, and returns a list of Event objects representing these events.

        Args:
            league (str): The league for which to scrape events (e.g., 'mlb', 'nba').
            driver (WebDriveer): The webdriver to scrapee the upcoming events.

        Returns:
            list[Event]: A list of Event objects representing the upcoming and live events for the specified league.
        '''
        events = []
        schedule_url = BaseScraper._get_schedule_base_url(league)
        driver.get(schedule_url)
        BaseScraper._locate_element_with_retries(driver, By.CSS_SELECTOR, 'div.ResponsiveTable')
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        tables = soup.find_all('div', class_='ResponsiveTable')
        for table in tables:
            title_element = table.find('div', class_='Table__Title')
            if title_element is None:
                continue

            date_text = title_element.text.strip()
            date = datetime.strptime(date_text, '%A, %B %d, %Y')

            rows = table.find_all('tr', class_='Table__TR')
            for row in rows:
                participants = row.find_all('span', class_='Table__Team')
                if len(participants) == 2:
                    away = BaseScraper._get_team_abbreviation(
                        league,
                        participants[0].find('a')['href'].split('/').pop().replace('-', ' ').upper()
                    )
                    home = BaseScraper._get_team_abbreviation(
                        league,
                        participants[1].find('a')['href'].split('/').pop().replace('-', ' ').upper()
                    )

                    time_element = row.find('td', class_='date__col')
                    if time_element is None:
                        continue

                    time_text = time_element.text.strip()
                    if time_text == 'LIVE':
                        active = True
                        start_time = date
                    else:
                        time_ = datetime.strptime(time_text, '%I:%M %p').time()
                        active = False
                        start_time = datetime.combine(date, time_)

                    events.append(ScrapedEvent(league, away, home, start_time, active))

        return events

    def _add_picks_to_matching_event(self, event, events, picks):
        '''
        Appends the given picks to the matching event in the list of events.

        This method searches through the list of events and appends the provided picks 
        to the event that matches the specified away team, home team, and event time.

        Args:
            event (Event): The event to be matched.
            events (list): List of Events.
            picks (list): List of Picks to be added to the matching event.

        Raises:
            ValueError: If no matching event is found in the list of events.
        '''
        for e in events:
            if e == event:
                e.books.append(ScrapedBook(self.book_name, picks))
                return
        
        raise ValueError(f'Matching event {event} not found.')


    def _get_book_base_url(self, league):
        '''
        Retrieves the base URL for the specified league from the stored book's base URLs.

        This method uses the `book_name` attribute of the instance to look up the base URL
        for the given league in the `BOOK_BASE_URL` dictionary.

        Args:
            league (str): The league for which to retrieve the base URL.

        Returns:
            str: The base URL associated with the specified league for the current sportsbook.

        Raises:
            KeyError: If the book name or league does not exist in the `BOOK_BASE_URL` dictionary.
        '''
        return BOOK_BASE_URL[self.book_name][league]

    @staticmethod    
    def _locate_element_with_retries(driver: WebDriver, by: By, value, multiple=False, retries=3, refresh=False, explicit_wait=2):
        '''
        Attempts to locate one or more elements on a webpage with retries and page refreshes if the element(s) is not found.

        Args:
            - driver: The Selenium WebDriver instance.
            - by: The method to locate elements (e.g., By.ID, By.CSS_SELECTOR, etc.).
            - value: The value of the locator (e.g., the ID, class name, CSS selector, etc.).
            - retries: The number of times to retry locating the element(s).
            - refresh: If the webdriver should refresh the page on the last retry.
            - multiple: Boolean indicating whether to locate a single element (False) or a list of elements (True).

        Returns:
            - The WebElement if locating a single element, or a list of WebElements if locating multiple elements.
            - Returns None if the element(s) are not found after all retries and refreshes.

        Raises:
            TimeoutException if the driver is unable to locate the element after the number of retries.
        '''
        for attempt in range(retries):
            try:
                if multiple:
                    elements = WebDriverWait(driver, Config.WEBDRIVER_WAIT_TIME).until(
                        EC.presence_of_all_elements_located((by, value))
                    )
                    if elements: # Ensure list is not empty
                        return elements
                else:
                    element = WebDriverWait(driver, Config.WEBDRIVER_WAIT_TIME).until(
                        EC.presence_of_element_located((by, value))
                    )
                    return element
            except (TimeoutException, NoSuchElementException) as e:
                logger.warning(f'Attempt {attempt + 1}/{retries}: Element(s) ({by}, {value}) not found.')
                if (attempt + 1) % retries == 0 and refresh:
                    driver.refresh()
                    time.sleep(explicit_wait)

        logger.error(f'Unable to locate element ({by}, {value}) after {retries} retries.')
        raise TimeoutException(f'Unable to locate element ({by}, {value}) after {retries} retries.')

    @staticmethod
    def _get_schedule_base_url(league):
        '''
        Retrieves the base URL for the schedule of a given league.

        Args:
            league (str): The league for which to retrieve the schedule base URL.

        Returns:
            str: The base URL for the league's schedule.

        Raises:
            KeyError if the league does not exist in the `SCHEDULE_BASE_URL~ dictionary.
        '''
        return SCHEDULE_BASE_URL[league]

    @staticmethod
    def _get_team_abbreviation(league, team_name):
        '''
        Converts any form of team name into its respective abbreviation.

        Args:
            league (str): The league of the team.
            team_name (str): The team name to convert.
            
        Returns:
            str: The abbreviation of the team.

        Raises:
            KeyError if the league and team name do not exist in the `TEAM_ACRONYMS` dictionary.
        '''
        return TEAM_ACRONYMS[league][team_name]

    @staticmethod
    def _normalize_market_name(market_name):
        team = None
        if ':' in market_name:
            market_name_parts = market_name.split(':')
            lhs = market_name_parts[0].strip().upper()
            rhs = market_name_parts[1].strip()
            if lhs in TEAM_ACRONYMS:
                team = TEAM_ACRONYMS[lhs]
                market_name = rhs

        normalized_market_name = (
            market_name.lower().replace(' ', '_').replace(':', '_')
                .replace('-', '_').replace('+', '_').replace('__', '_')
        )
        normalized_market_name_parts = normalized_market_name.split('_')
        if team:
            normalized_market_name_parts.insert(0, 'team')
        
        market_name = '_'.join(normalized_market_name_parts).strip('_')
        return MARKET_MAPPINGS[market_name], team

    @staticmethod
    @abstractmethod
    def _format_event_time(date, time=None):
        '''
        Converts a date and time from the sportsbook format into the general ISO 8601 format.

        Args:
            date (str): The date of the event. Can be in various formats such as 'Today', 'Tomorrow', or 'MM/DD/YY'.
            time (str, optional): The time of the event. If not provided, the time will be set to the start of the day.

        Returns:
            str: The event date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
        '''
        pass

    @staticmethod
    @abstractmethod
    def _get_event_info(soup: BeautifulSoup):
        '''
        Extracts event information from an event page on the sportsbook.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the event page.

        Returns:
            tuple: A tuple containing:
                - away_team (str): Abbreviation of the away team.
                - home_team (str): Abbreviation of the home team.
                - event_time (str): Event time in ISO 8601 format.
                - active (bool): Flag indicating if the event is active or not.
        '''
        pass