from abc import ABC, abstractmethod
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config

from .models import ScrapedEvent, ScrapedBook, ScrapedPick

from utils import LEAGUES, TEAM_ACRONYMS, SCHEDULE_BASE_URL, BOOK_BASE_URL, MARKET_MAPPINGS

class BaseScraper(ABC):

    @staticmethod
    def scrape_upcoming_events(league):
        '''
        Scrapes the list of upcoming and live events for the specified league from the schedule page.

        This method navigates to the schedule page for the given league, parses the page to extract 
        event information, and returns a list of Event objects representing these events.

        Args:
            league (str): The league for which to scrape events (e.g., 'mlb', 'nba').

        Returns:
            list[Event]: A list of Event objects representing the upcoming and live events for the specified league.
        '''
        driver = Config.get_driver()
        events = []
        schedule_url = BaseScraper._get_schedule_base_url(league)
        driver.get(schedule_url)
        WebDriverWait(driver, Config.WEBDRIVER_WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.ResponsiveTable'))
        )
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
                        participants[0].find('a')['href'].split('/').pop().replace('-', ' ').upper()
                    )
                    home = BaseScraper._get_team_abbreviation(
                        participants[1].find('a')['href'].split('/').pop().replace('-', ' ').upper()
                    )

                    time_element = row.find('td', class_='date__col')
                    if time_element is None:
                        continue

                    time_text = time_element.text.strip()
                    if time_text == 'LIVE':
                        active = True
                        start_time = date.isoformat()
                    else:
                        time_ = datetime.strptime(time_text, '%I:%M %p').time()
                        active = False
                        start_time = datetime.combine(date, time_).isoformat()

                    events.append(ScrapedEvent(league, away, home, start_time, active))

        driver.quit()

        return events

    @staticmethod
    def _fuzzy_find_event(event_info, events, min_tolerance=10):
        '''
        Perform a fuzzy search to find an event that matches the given event information within a specified time tolerance.

        Given the variability in the exact start time of sporting events, this method compares the provided event information
        `event_info` with a list of existing events `events` to find a match. It checks if the away team, home team, and 
        event status match exactly, and if the event start time falls within a given time tolerance.
        
        Args:
            event_info (tuple): A tuple containing the following elements:
                - away_team (str): The name of the away team.
                - home_team (str): The name of the home team.
                - start_time (str): The ISO 8601 formatted start time of the event.
                - active (bool): The status of the event, indicating whether it is active.
            events (list): A list of event objects to search through. Each event object is expected to have the following attributes:
                - away_team (str): The name of the away team.
                - home_team (str): The name of the home team.
                - start_time (str): The ISO 8601 formatted start time of the event.
                - active (bool): The status of the event.
            min_tolerance (int, optional): The maximum allowable time difference in minutes between the event start times. Defaults to 5 minutes.
            
        Returns:
            tuple: A tuple containing the matching event's away team, home team, start time, and active status if a match is found.
        
        Raises:
            ValueError: If no matching event is found within the specified time tolerance.
        '''
        away_team, home_team, start_time, active = event_info
        start_time = datetime.fromisoformat(start_time)

        for event in events:
            event_start_time = datetime.fromisoformat(event.start_time)
            time_difference = abs((event_start_time - start_time).total_seconds() / 60)
            if (
                event.away_team == away_team and 
                event.home_team == home_team and 
                time_difference <= min_tolerance and
                event.active == active
            ):
                return event.away_team, event.home_team, event.start_time, event.active

        raise ValueError(f'Event {away_team}@{home_team}_{start_time} not found.')

    @staticmethod
    def _add_picks_to_matching_event(event, book_name, events, picks):
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
                e.books.append(ScrapedBook(book_name, picks))
                return
        raise ValueError(f'Matching event {event} not found.')

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

        Raises:
            KeyError if the league does not exist in the `SCHEDULE_BASE_URL~ dictionary.
        '''
        return SCHEDULE_BASE_URL[league]

    @staticmethod
    def _get_team_abbreviation(team_name):
        '''
        Converts any form of team name into its respective abbreviation.

        Args:
            team_name (str): The team name to convert.
            
        Returns:
            str: The abbreviation of the team.

        Raises:
            KeyError if the team name does not exist in the `TEAM_ACRONYMS~ dictionary.
        '''
        return TEAM_ACRONYMS[team_name]

    @staticmethod
    def _get_market_name(market_name):
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

    @staticmethod
    @abstractmethod
    def _scrape_events(league, events):
        pass

    @staticmethod
    @abstractmethod
    def scrape_event_page(event_url, event, driver=None):
        '''
        Scrapes an event page for a certain sportsbook.

        This function scrapes all available game and player prop odds for this event,
        and stores the data in a list.

        Paramters:
            event_url (str): The url of the event page on this sportsbook.

        Returns:
            list[Event]: 
           
        '''
        pass

    @staticmethod
    @abstractmethod
    def _scrape_block_picks(soup: BeautifulSoup):
        '''
        Scrapes betting options from a specific block element on the sportsbook page.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object of the innerHTML of the block.

        Returns:
            list: A list of all available betting options in this block.
        '''
        pass