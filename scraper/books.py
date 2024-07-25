from abc import ABC, abstractmethod
import pandas as pd
from selenium import webdriver, By, WebDriverWait
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from bookutil import books, team_acronyms, target_props
import hashlib

class BookScraper(ABC):
    def __init__(self, driver: webdriver, book_name: str):
        self.driver = driver
        self.book_name = book_name

    @abstractmethod
    def navigate_and_scrape(self, leagues: list) -> list:
        '''
        Get's all the odds for this sports book in the given leagues.

        Navigates a sports book starting from the base url and collects a list
        of odds data for each event happening in the requested leagues.

        Parameters:
            leagues (list): a list of the desired leagues to get odds data from.

        Returns:
            list: sportsbook odds
        '''
        pass


    @staticmethod
    def __get_base_url(sportsbook, league) -> str:
        '''
            Gets the base URL that the driver should navigate to in order
        to locate all of the event odds,
        
        Parameters:
                sportsbook (str): Sports book domain for the URL.
            league (str): The sports league.
            
        Returns:
                str: Base url for the league page for the given sportsbook.
        '''
        return books[sportsbook][league]
    
    @staticmethod
    def __get_team_abbreviation(team_name):
        '''
        Converts any form of team name into its 3-letter abbreviation.

        Parameters:
            team_name (str): The team name to convert.
            
        Returns:
            str: The 3-letter abbreviation of the team.
        '''
        return team_acronyms[team_name]


    @abstractmethod
    @staticmethod
    def __format_event_datetime(self, date: str, time: str) -> str:
        '''
        Converts a date in a specific format according to the sportsbook
        into the general format YYYY-MM-DD.

        Parameters:
            date (str): event date.
            time (str): event time.
        
        Returns:
            str: formatted date in the format YYYY-MM-DD.
        '''
        pass


    @abstractmethod
    def __get_event_info(self, html: str) -> str:
        '''
        Gets the event information from an event page on the sports book.

        Parameters:
            html (str): the raw HTML of the event page. 

        Returns:
            tuple: Away, Home, Datetime
        '''
        pass


    @abstractmethod
    def __scrape_event(self, league: str) -> list:
        '''
        Scrapes an event page for a certain sports book. 

        This function scrapes all of the available game and player prop odds
        for this event, and stores the data in a list.

        Parameters:
            league (str): the sports league of the event.

        Returns:
            list: all available betting options for an event.

        Example:
            >>> data = scrape_event()
            >>> print(data)
            [
                # Moneyline
                {
                    'event': 'BOS@COL_2024-07-24_07:30',
                    'key': '979fdc3b0bba27b9b3da229d9cd3302f'
                    'timestamp': '2024-07-24T13:56'
                    'book' 'BetMGM',
                    'sport': 'Baseball'
                    'league': 'MLB',
                    'type': 'moneyline',
                    'team': 'BOS',
                    'line': None,
                    'odds': -130,
                    'player': None,
                    'prop': None,
                    
                },
                # Spread
                {
                    'event': 'BOS@COL_2024-07-24_07:30',
                    'key': '979fdc3b0bba27b9b3da229d9cd3302f'
                    'book' 'BetMGM',
                    'sport': 'Baseball'
                    'league': 'MLB',
                    'type': 'spread',
                    'team': 'BOS',
                    'line': -1.5,
                    'odds': 100,
                    'player': None,
                    'prop': None,
                    'timestamp': '2024-07-24T13:56'
                }, 
                # Total
                {
                    'event': 'BOS@COL_2024-07-24_07:30',
                    'key': '979fdc3b0bba27b9b3da229d9cd3302f'
                    'book' 'BetMGM',
                    'sport': 'Baseball'
                    'league': 'MLB',
                    'type': 'over',
                    'team': None,
                    'line': 11,
                    'odds': 100,
                    'player': None,
                    'prop': None,
                    'timestamp': '2024-07-24T13:56'
                    
                }, 
                # Player Prop
                {
                    'event': 'BOS@COL_2024-07-24_07:30',
                    'key': '979fdc3b0bba27b9b3da229d9cd3302f'
                    'book' 'BetMGM',
                    'sport': 'Baseball'
                    'league': 'MLB',
                    'type': None,
                    'team': None,
                    'line': 6.5,
                    'odds': -115
                    'player': 'Nick Pivetta',
                    'prop': 'Over Strikeouts',
                    'timestamp': '2024-07-24T13:56'
                },
                ...
            ]
        '''
        pass

    @abstractmethod
    def __scrape_block(self, block) -> str:
        pass


class BetMGMScraper(BookScraper):
    def __init__(self, driver: webdriver):
        super().__init__(driver, 'BetMGM')

    def navigate_and_scrape(self, leagues: list) -> list:
        data = []
        for league in leagues:
            base_url = self.__get_base_url(self.book_name, league)
            self.driver.get(base_url)

        self.driver.close()
        return data

    
    def __get_event_info(self, html: str) -> str:
        soup = BeautifulSoup(html, 'lxml')

        participants = soup.find_all('div', class_='participant-name')
        # TODO: Convert participant names into standard abbreviations
        try:
            date = soup.find('span', class_='date').text
            time = soup.find('span', class_='time').text
            datetime_str = self.__format_event_datetime(date, time)
        except:
            # If the event date or time element is not present, then the event is live.
            date = datetime.today().strftime('%Y-%m-%d')
            datetime_str = f'{date}_LIVE'
        return participants[0], participants[1], datetime


    def __format_event_datetime(self, date: str, time: str) -> str:
        if date.lower() == 'today':
            date = datetime.now().date()
        elif date.lower() == 'tomorrow':
            date = (datetime.now() + timedelta(1)).date()
        else:
            date = datetime.strptime(date, '%m/%d/%y').date()
        
        time = datetime.strptime(time, '%I:%M %p').time()

        formatted_datetime = datetime.combine(date, time)
        return formatted_datetime.strftime('%Y-%m-%d_%H:%M')

    
    def __scrape_event(self, league: str) -> list:
        data = []
        html = self.driver.page_source
        away, home, datetime_str = self.__get_event_info(html)
        event_title = f'{away}@{home}_{datetime_str}'
    
        blocks = self.driver.find_elements(By.CSS_SELECTOR, 'ms-option-panel.option-panel')
        for block in blocks:
            block_data = self.__scrape_block(block)
            data.extend(block_data)

        return data


    def __scrape_block(self, block) -> list:
        # Make sure the block is open before getting HTML content.
        is_closed = block.find_element(By.CSS_SELECTOR, 'div.option-group-header-chevron span') \
                         .get_attribute('class') == 'theme-down'
        if is_closed:
            expand_button = block.find_element(By.CSS_SELEECTOR, 'div.option-group-name.clickable')
            expand_button.click()
    
        # If there is a show more button, click it.
        show_more_button = self.driver.find_elements(By.CSS_SELECTOR, 'div.show-more-less-button')
        if show_more_button:
            show_more_button[0].click()

        tabs = []
        scroll_bar = block.find_elements(By.TAG_NAME, 'ms-scroll-adapter')
        if scroll_bar:
            tab_links = block.find_elements(By.CSS_SELECTOR, 'a.link-without-count')
        
        
        block_html = block.get_attribute('innerHTML')
        soup = BeautifulSoup(block_html, 'lxml')

        block_title = soup.find('span', class_='market-name').text
        block_type = soup.find('div', class_='option-group-container').get_attribute_list('class')[1]

        match block_type:
            # Game Lines
            case 'six-pack-container':
                spreads, totals, moneylines = [], [], []

                option_rows = soup.find_all('div', class_='option-row')
                for row in option_rows:
                    options = row.find_all('ms-option', class_='option')

                    for option in options:
                        pick = option.find('ms-event-pick', _class='option-pick')
                        if pick:
                            name = pick.find('div', class_='name')
                            value = pick.find('div', class_='value')
                            
                            if name and '+' in name.text or '-' in name.text:
                                spread_line = int(name.text.replace('+', ''))
                                spread_value = int(value.text.replace('+', ''))
                                spreads.append((spread_line, spread_value))
                            elif name and 'O' in name.text or 'U' in name.text:
                                ou = 'Over' if 'O' in name.text else 'Under'
                                total_line = int(name.text.replace('O', '').replace('U', '').strip())
                                total_value = int(value.text.replace('+', ''))
                                totals.append((ou, total_line, total_value))
                            else:
                                moneylines.append(int(value.replace('+', '')))
            case 'over_under_container':
                return []
            case _:
                return []





            




            







