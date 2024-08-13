from abc import ABC, abstractmethod
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import time

from .models import Event, Pick

from exceptions import EventLengthMismatchError
from utils import LEAGUES, TEAM_ACRONYMS, SCHEDULE_BASE_URL, BOOK_BASE_URL

class BaseScraper(ABC):
    def __init__(self, driver: WebDriver, book_name):
        self.driver = driver
        self.book_name = book_name
        self.wait = WebDriverWait(self.driver, 10)

    def scrape_league_events(self, league):
        '''
        Scrapes the list of upcoming and live events for the specified league from the schedule page.

        This method navigates to the schedule page for the given league, parses the page to extract 
        event information, and returns a list of Event objects representing these events.

        Args:
            league (str): The league for which to scrape events (e.g., 'mlb', 'nba').

        Returns:
            list: A list of Event objects representing the upcoming and live events for the specified league.
        '''
        events = []
        schedule_url = self._get_schedule_base_url(league)
        self.driver.get(schedule_url)
        self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.ResponsiveTable'))
        )
        html = self.driver.page_source
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
                    away = BaseScraper._get_team_abbreviation(participants[0].text.strip().upper())
                    home = BaseScraper._get_team_abbreviation(participants[1].text.strip().upper())

                    time_element = row.find('td', class_='date__col')
                    if time_element is None:
                        continue

                    time_text = time_element.text.strip()
                    if time_text == 'LIVE':
                        is_live = True
                        start_time = date.isoformat()
                    else:
                        time = datetime.strptime(time_text, '%I:%M %p').time()
                        is_live = False
                        start_time = datetime.combine(date, time).isoformat()

                    events.append(Event(league, away, home, start_time, is_live))

        return events

    def _fuzzy_find_event(self, events, event_info, min_tolerance=5):
        away_team, home_team, start_time, is_live = event_info
        start_time = datetime.fromisoformat(start_time)

        for event in events:
            event_start_time = datetime.fromisoformat(event.start_time)
            time_difference = abs((event_start_time - start_time).total_seconds() / 60)
            if (
                event.away_team == away_team and 
                event.home_team == home_team and 
                time_difference <= min_tolerance and
                event.is_live == is_live
            ):
                return event.away_team, event.home_team, event.start_time, event.is_live

    def _load_events_with_retries(self, locator: tuple, expected_length, max_retries=3, wait_time=5):
        '''
        Attempts to load the list of events from the sportsbook page multiple times 
        until the expected number of events is loaded or the maximum number of retries is reached.

        Args:
            locator (tuple): Locator for the elements representing events on the page, used by Selenium.
            expected_length (int): The expected number of event elements to be loaded.
            max_retries (int): Maximum number of retry attempts if the expected number of events is not loaded.
            wait_time (int): The amount of time to wait for events to load between retries.

        Returns:
            list: List of WebElement objects representing the loaded events.

        Raises:
            EventLengthMismatchError: If the expected number of events is not loaded within the maximum number of retries.
        '''
        for _ in range(max_retries):
            scraped_events = self.wait.until(
                EC.presence_of_all_elements_located(locator)
            )
            if len(scraped_events) != expected_length:
                time.sleep(wait_time)
            else:
                return scraped_events
        raise EventLengthMismatchError(f'Expected: {expected_length}, Actual: {len(scraped_events)}.')

    def _add_picks_to_matching_event(self, events, event_info, picks):
        '''
        Appends the given picks to the matching event in the list of events.

        This method searches through the list of events and appends the provided picks 
        to the event that matches the specified away team, home team, and event time.

        Args:
            events (list): List of event dictionaries.
            event_info (tuple): Tuple containing event information to match.
            picks (dict): Dictionary containing the picks to append to the matching event.

        Raises:
            ValueError: If no matching event is found in the list of events.
        '''
        criteria = {
            'away_team': event_info[0], 'home_team': event_info[1], 
            'start_time': event_info[2], 'is_live': event_info[3]
        }
        for e in events:
            if all(e.get(k) == v for k, v in criteria.items()):
                e.books.append({
                    'title': self.book_name,
                    'last_update': datetime.now().isoformat(),
                    'picks': [p.to_dict() for p in picks]
                })
                return
        raise ValueError('Matching event not found.')

    @staticmethod
    def _get_book_base_url(book, league):
        '''
        Retrieves the base URL for the specified league from the stored book's base URLs.

        This method uses the `book_name` attribute of the instance to look up the base URL
        for the given league in the `BOOK_BASE_URL` dictionary.

        Args:
            book (str): The base URL of the sports book.
            league (str): The league for which to retrieve the base URL.

        Returns:
            str: The base URL associated with the specified league for the current sportsbook.

        Raises:
            KeyError: If the book name or league does not exist in the `BOOK_BASE_URL` dictionary.
        '''
        return BOOK_BASE_URL[book][league]

    @staticmethod
    def _get_schedule_base_url(league):
        '''
        Retrieves the base URL for the schedule of a given league.

        Args:
            league (str): The league for which to retrieve the schedule base URL.

        Returns:
            str: The base URL for the league's schedule.
        '''
        return SCHEDULE_BASE_URL[league]

    @staticmethod
    def _get_team_abbreviation(team_name):
        '''
        Converts any form of team name into its 3-letter abbreviation.

        Args:
            team_name (str): The team name to convert.
            
        Returns:
            str: The 3-letter abbreviation of the team.
        '''
        return TEAM_ACRONYMS[team_name]

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

    @abstractmethod
    def _get_event_info(self, soup: BeautifulSoup):
        '''
        Extracts event information from an event page on the sportsbook.

        Args:
            soup (BeautifulSoup): Parsed HTML content of the event page.

        Returns:
            tuple: A tuple containing:
                - away_team (str): Abbreviation of the away team.
                - home_team (str): Abbreviation of the home team.
                - event_time (str): Event time in ISO 8601 format.
                - is_live (bool): A flag indicating if the event is currently live.
        '''
        pass


    @abstractmethod
    def scrape_odds(self, league, events):
        '''
        Scrapes all the picks and their odds for this sportsbook in the given league.

        Navigates the sportsbook and for each league, starting from the league's base URL,
        scrapes a list of all possible picks and their odds for each event happening in the requested leagues.

        Args:
            league (str): The league for which to scrape odds data.
            events (list): A list of Event objects representing the events to scrape.

        '''
        pass

    @abstractmethod
    def _scrape_event(self, event_info):
        '''
        Scrapes an event page for a certain sportsbook.

        This function scrapes all available game and player prop odds for this event,
        and stores the data in a list.

        Args:
            event_info (tuple): A tuple containing:
                - away_team (str): Abbreviation of the away team.
                - home_team (str): Abbreviation of the home team.
                - start_time (str): Event time in ISO 8601 format.

        Returns:
            dict: A dictionary containing the book name, last update time, and a list of all available betting options for the event.
        '''
        pass

    @abstractmethod
    def _scrape_block(self, block: WebElement, event_info):
        '''
        Scrapes betting options from a specific block element on the sportsbook page.

        Args:
            block (WebElement): The web element containing the betting options.
            event_info (tuple): A tuple containing:
                - away_team (str): Abbreviation of the away team.
                - home_team (str): Abbreviation of the home team.
                - start_time (str): Event time in ISO 8601 format.

        Returns:
            list: A list of all available betting options in this block.
        '''
        pass