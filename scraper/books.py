from abc import ABC, abstractmethod
import pandas as pd
from selenium import webdriver, By, WebDriverWait
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class BookScraper(ABC):

    def __init__(self, driver: webdriver, book_name: str, base_url: str):
        self.driver = driver
        self.book_name = book_name
        self.base_url = base_url

    @abstractmethod
    def format_event_datetime(self, date: str, time: str) -> str:
        pass

    @abstractmethod
    def get_event_title(self, html: str) -> str:
        pass

    @abstractmethod
    def navigate_and_scrape(self, leagues: list) -> list:
        '''
        Get's all the odds for this sports book in the given leagues.

        Navigates a sports book starting from the base url and collects a list
        of odds data for each event happening in the requested leagues.

        Parameters:
            leagues: A list of the desired leagues to get odds data from.

        Returns:
            list of dictionaries
        '''
        pass

    @abstractmethod
    def scrape_event(self) -> list:
        '''
        Scrapes an event page for a certain sports book. 

        This function scrapes all of the available game and player prop odds
        for this event, and stores the data in a list.

        Returns:
            list of dictionaries

        Example:
            >>> data = scrape_event()
            >>> print(data)
            [
                # Moneyline
                {
                    'book' 'BetMGM',
                    'league': 'MLB',
                    'event': 'BOS@COL 2024-07-24-07:30',
                    'type': 'moneyline',
                    'team': 'BOS',
                    'line': None,
                    'odds': -130,
                    'player': None,
                    'prop': None,
                    'timestamp': '2024-07-24T13:56'
                },
                # Spread
                {
                    'book' 'BetMGM',
                    'league': 'MLB',
                    'event': 'BOS@COL 2024-07-24-07:30',
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
                    'book' 'BetMGM',
                    'league': 'MLB',
                    'event': 'BOS@COL 2024-07-24-07:30',
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
                    'book' 'BetMGM',
                    'league': 'MLB',
                    'event': 'BOS@COL 2024-07-24-07:30',
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

        

class BetMGMScraper(BookScraper):

    def __init__(self, driver: webdriver):
        super().__init__(driver, 'BetMGM', 'https://sports.il.betmgm.com/en/sports')

    def get_event_title(self, html: str) -> str:
        soup = BeautifulSoup(html, 'lxml')

        participants = soup.find_all('div', class_='participant-name')
        # TODO: Convert participant names into standard abbreviations
        try:
            date = soup.find('span', class_='date').text
            time = soup.find('span', class_='time').text
            datetime_str = self.format_event_datetime(date, time)
        except:
            # If the event date or time element is not present, then the event is live.
            date = datetime.today().strftime('%Y-%m-%d')
            datetime_str = f'{date}-LIVE'
        
        return f'{participants[0].text}@{participants[1].text} {datetime_str}'

    def format_event_datetime(self, date: str, time: str) -> str:
        if date.lower() == 'today':
            date = datetime.now().date()
        elif date.lower() == 'tomorrow':
            date = (datetime.now() + timedelta(1)).date()
        else:
            date = datetime.strptime(date, '%m/%d/%y').date()
        
        time = datetime.strptime(time, '%I:%M %p').time()

        formatted_datetime = datetime.combine(date, time)
        return formatted_datetime.strftime('%Y-%m-%d-%H:%M')

    def navigate_and_scrape(self) -> list:
        data = []
        self.driver.get(self.base_url)

        self.driver.close()
        return data

    def scrape_event(self) -> list:
        data = []
        html = self.driver.page_source
        event_title = self.get_event_title(html)
        blocks = self.driver.find_elements(By.CSS_SELECTOR, 'ms-option-panel.option-panel')
        for i, block in enumerate(blocks):
            if i == 0:
                block_html = block.get_attribute('innerHTML')
                soup = BeautifulSoup(block_html, 'lxml')
                keys = soup.find_all('six-pack-player-name')



                continue

            show_more_button = self.driver.find_elements(By.CSS_SELECTOR, 'div.show-more-less-button')
            if show_more_button:
                show_more_button[0].click()

            prop_tabs = block.find_elements(By.CSS_SELECTOR, 'a.link-without-count')
            for tab in prop_tabs:
                # Click the prop tab
                tab.click()

                # Parse the updated block content
                block_html = block.get_attribute('innerHTML')
                soup = BeautifulSoup(block_html, 'lxml')




            




            







