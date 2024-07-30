from abc import ABC, abstractmethod
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from scraper.bookutil import books, target_props, team_acronyms
import hashlib
import itertools

class BookScraper(ABC):
	def __init__(self, driver: WebDriver, book_name: str):
		self.driver = driver
		self.book_name = book_name


	def scrape(self, leagues: list) -> list:
		'''
		Get's all the picks and their odds for this sports book in the given leagues.

		Navigates a sports book and for each league, starting from the league's base URL,
		scrapes a list of every possible picks and it's odds for each event happening in 
		the requested leagues.

		Parameters:
			leagues (list): a list of the desired leagues to get odds data from.

		Returns:
			list: sportsbook odds
		'''
		picks = []
		for league in leagues:
			try:
				league_picks = self._scrape_league(league)
				picks.extend(league_picks)
			except Exception as e:
				print(f'Error getting picks for league {league}: {e}')

		self.driver.close()
		return picks


	@staticmethod
	def _create_pick(event_title, book_name, league, pick_type, 
					  team, line, odds, player, prop) -> dict:
		'''
		Creates a pick dictionary with a unique key based on the input parameters.

		Parameters:
			event_title (str): The title of the sporting event.
			book_name (str): The name of the sportsbook.
			league (str): The league associated with the event.
			pick_type (str): The type of pick (e.g., spread, moneyline, total).
			team (str): The team associated with the pick.
			line (str): The betting line for the pick.
			odds (str): The odds associated with the pick.
			player (str): The player associated with the pick, if any.
			prop (str): The prop associated with the pick, if any.

		Returns:
			dict: A dictionary containing the pick details, including a unique key and timestamp.
		
		Note:
			The unique key is generated using a SHA-256 hash of a string formed by concatenating
			the input parameters with underscores. The timestamp is the current datetime.
		'''
		pick_values = [event_title, league, pick_type,
					   team, line, odds, player, prop]

		pick_string = '_'.join(str(p) if p is not None else '' for p in pick_values)
		key = hashlib.sha256(pick_string.encode()).hexdigest()
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

		return {
			'event': event_title,
			'key': key,
			'book': book_name,
			'league': league,
			'type': pick_type,
			'team': team,
			'line': line,
			'odds': odds,
			'player': player,
			'prop': prop,
			'timestamp': timestamp,
		}

	def _get_base_url(self, league) -> str:
		'''
		Gets the base URL that the driver should navigate to in order
		to locate all of the event odds,
		
		Parameters:
			sportsbook (str): Sports book domain for the URL.
			league (str): The sports league.
			
		Returns:
				str: Base url for the league page for the given sportsbook.
		'''
		return books[self.book_name][league]
	
	@staticmethod
	def _get_team_abbreviation(team_name):
		'''
		Converts any form of team name into its 3-letter abbreviation.

		Parameters:
			team_name (str): The team name to convert.
			
		Returns:
			str: The 3-letter abbreviation of the team.
		'''
		return team_acronyms[team_name]


	@staticmethod
	@abstractmethod
	def _format_event_datetime(self, date: str, time: str) -> str:
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
	def _get_event_info(self, html: str) -> str:
		'''
		Gets the event information from an event page on the sports book.

		Parameters:
			html (str): the raw HTML of the event page. 

		Returns:
			tuple: Away, Home, Datetime
		'''
		pass


	@abstractmethod
	def _scrape_league(self, league: str) -> list:
		'''Scrapes all the possible picks and their odds for the league on this sports book.'''
		pass
		 

	@abstractmethod
	def _scrape_event(self, league: str) -> list:
		'''
		Scrapes an event page for a certain sports book. 

		This function scrapes all of the available game and player prop odds
		for this event, and stores the data in a list.

		Parameters:
			league (str): the sports league of the event.

		Returns:
			list: all available betting options for an event.
		'''
		pass

	@abstractmethod
	def _scrape_block(self, block, league, event_title) -> str:
		pass


class BetMGMScraper(BookScraper):
    def __init__(self, driver: WebDriver):
        super().__init__(driver, 'BetMGM')


    def _get_event_info(self, html: str) -> tuple:
        soup = BeautifulSoup(html, 'lxml')
        participants = soup.find_all('div', class_='participant-name')
        if len(participants) < 2:
            raise ValueError("Not enough participant information found")

        participant1 = self._get_team_abbreviation(participants[0].text.strip().upper())
        participant2 = self._get_team_abbreviation(participants[1].text.strip().upper())

        try:
            date = soup.find('span', class_='date').text.strip()
            time = soup.find('span', class_='time').text.strip()
            datetime_ = self._format_event_datetime(date, time)
        except Exception as e:
            print(f'Error formatting event datetime: {e}')
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

        # Wait for main content to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'main'))
        )

        # Wait for each clickable event to load
        events = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ms-six-pack-event.grid-event'))
        )

        for event in events:
            try:
                event.click()
                event_picks = self._scrape_event(league)
                league_picks.extend(event_picks)
                self.driver.back()
                # Wait for events to load back in
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ms-six-pack-event.grid-event'))
                )
            except Exception as e:
                print(f'Error scraping event: {e}')

        return league_picks


    def _scrape_event(self, league: str) -> list:
        event_picks = []

        # Wait for game header to load
        WebDriverWait(self.driver, 10).until(
             EC.presence_of_element_located((By.CSS_SELECTOR, 'div.main-score-container'))
        )

        html = self.driver.page_source
        away, home, datetime_ = self._get_event_info(html)
        event_title = f'{away}@{home}_{datetime_}'

        print(f'Scraping event: {event_title}')

        blocks = WebDriverWait(self.driver, 10).until(
             EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ms-option-panel.option-panel'))
        )

        for block in blocks:
            try:
                block_picks = self._scrape_block(block, league, event_title)
                event_picks.extend(block_picks)
            except Exception as e:
                print(f'Error scraping block" {e}')

        return event_picks


    def _scrape_block(self, block: WebElement, league, event_title) -> list:
        block_picks = []

        # Expand block if it is closed
        try:
            is_closed = block.find_element(By.CSS_SELECTOR, 'div.option-group-header-chevron span').get_attribute('class') == 'theme-down'
            if is_closed:
                expand_button = block.find_element(By.CSS_SELECTOR, 'div.option-group-name.clickable')
                expand_button.click()
        except Exception as e:
            print(f'Error expanding block: {e}')

        # If there is a show more button, click it
        try:
            show_more_button = block.find_elements(By.CSS_SELECTOR, 'div.show-more-less-button')
            if show_more_button:
                show_more_button[0].click()
        except Exception as e:
            print(f'Error clicking show more button: {e}')

        try:
            block_title = block.find_element(By.CSS_SELECTOR, 'span.market-name').text.upper()
            block_type = block.find_element(By.CSS_SELECTOR, 'div.option-group-container').get_attribute('class').split()[1]

            print(f'Scraping block: {block_title} ({block_type})')

            tabs = []
            scroll_bar = block.find_elements(By.TAG_NAME, 'ms-scroll-adapter')
            if scroll_bar:
                tab_links = block.find_elements(By.CSS_SELECTOR, 'a.link-without-count')
                tabs.extend(tab_links)
            else:
                tabs.append(None)

            for tab in tabs:
                if tab:
                    tab.click()

                block_html = block.get_attribute('innerHTML')
                soup = BeautifulSoup(block_html, 'lxml')

                match block_type:
                    case 'six-pack-container':
                        spreads, totals, moneylines = [], [], []
                        rows = soup.find_all('div', class_='option-row')
                        if len(rows) != 2:
                             raise ValueError('Game lines must have 2 rows')

                        for row in rows:
                            team_text = row.find('div', class_='six-pack-player-name').text.strip().upper()
                            team = self._get_team_abbreviation(team_text)
                            options = row.find_all('ms-option', class_='option')

                            for option in options:
                                option_pick = option.find('ms-event-pick', class_='option-pick')
                                if option_pick:
                                    name = option_pick.find('div', class_='name')
                                    value = option_pick.find('div', class_='value')

                                    if name and ('+' in name.text or '-' in name.text):
                                        line = float(name.text.replace('+', ''))
                                        odds = int(value.text.replace('+', ''))
                                        spreads.append(('SPREAD', team, line, odds))
                                    elif name and ('O' in name.text or 'U' in name.text):
                                        ou = 'TOTAL_OVER' if 'O' in name.text else 'TOTAL_UNDER'
                                        line = float(name.text.replace('O', '').replace('U', '').strip())
                                        odds = int(value.text.replace('+', ''))
                                        totals.append((ou, team, line, odds))
                                    else:
                                        odds = int(value.text.replace('+', ''))
                                        moneylines.append(('MONEYLINE', team, None, odds))

                        six_pack_picks = itertools.chain(spreads, totals, moneylines)
                        for game_line in six_pack_picks:
                            pick = self._create_pick(event_title, self.book_name, league,
                                                     game_line[0], game_line[1], game_line[2], game_line[3],
                                                     None, None)
                            block_picks.append(pick)

                    case 'over-under-container':
                        if ':' in block_title:
                            title_parts = block_title.split(':')
                            team = self._get_team_abbreviation(title_parts[0].strip())
                            pick_type = title_parts[1].strip().replace(' ', '-')
                        else:
                            team = None
                            pick_type = block_title.strip().replace(' ', '-')

                        lines = soup.find_all('div', class_='attribute_key')
                        options = soup.find_all('ms-option', class_='option')
                        for i, option in enumerate(options):
                            line = float(lines[i / 2].text)
                            pick_type += f'_{'OVER' if i % 2 == 0 else 'UNDER'}'

                            option_pick = option.find('ms-event-pick', class_='option-pick')
                            if option_pick:
                                odds = int(option_pick.find('ms-font-resizer').text.replace('+', '').strip())
                                pick = self._create_pick(event_title, self.book_name, league,
                                                         pick_type, team, line, odds,
                                                         None, None)

                                block_picks.append(pick)

                    case 'player-props-container':
                        players = soup.find_all('div', class_='player-props-player-name')
                        options = soup.find_all('ms-option', class_='option')
                        pick_type = 'PLAYER-PROP'
                        for i, option in enumerate(options):
                            player = players[i % 2].text
                            prop = f'{tab.text.replace(' ', '-').upper()}_{'OVER' if i % 2 == 0 else 'UNDER'}'
                            option_pick = option.find('ms-event-pick', class_='option-pick')
                            if option_pick:
                                line = float(option_pick.find('div', class_='name').text
                                             .replace('Over', '')
                                             .replace('Under', '')
                                             .strip())
                                odds = int(option_pick.find('div', class_='value').text.replace('+', ''))
                                pick = self._create_pick(event_title, self.book_name, league,
                                                         pick_type, None, line, odds,
                                                         player, prop)
                                block_picks.append(pick)
                    case _:
                        print(f'Unsupported block type: {block_type}')

        except Exception as e:
            print(f'Error scraping block details: {e}')

        return block_picks