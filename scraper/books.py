from abc import ABC, abstractmethod
import pandas as pd
from selenium import webdriver, By, WebDriverWait
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from bookutil import books, team_acronyms, target_props
import hashlib
import itertools

class BookScraper(ABC):
	def __init__(self, driver: webdriver, book_name: str):
		self.driver = driver
		self.book_name = book_name

	@abstractmethod
	def navigate_and_scrape(self, leagues: list) -> list:
		'''
		Get's all the picks and their odds for this sports book in the given leagues.

		Navigates a sports book starting from the base url and collects a list
		of odds data for each event happening in the requested leagues.

		Parameters:
			leagues (list): a list of the desired leagues to get odds data from.

		Returns:
			list: sportsbook odds
		'''
		pass

		 
	@staticmethod
	def __create_pick(event_title, book_name, league, pick_type, 
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
		pick_values = [event_title, book_name, league, pick_type,
					   team, line, odds, player, prop, timestamp]

		pick_string = '_'.join(str(p) if p is not None else '' for p in pick_values)
		key = hashlib.sha256(pick_string.encode()).hexdigest()
		timestamp = datetime.datetime.now()

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
		'''
		pass

	@abstractmethod
	def __scrape_block(self, block, league, event_title) -> str:
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


	def __scrape_block(self, block, league, event_title) -> list:
		block_picks = []

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

		# TODO: If there is a scroll bar, iterate over each tab link and click it.
		tabs = []
		scroll_bar = block.find_elements(By.TAG_NAME, 'ms-scroll-adapter')
		if scroll_bar:
			tab_links = block.find_elements(By.CSS_SELECTOR, 'a.link-without-count')

		
		block_html = block.get_attribute('innerHTML')
		soup = BeautifulSoup(block_html, 'lxml')

		block_title = soup.find('span', class_='market-name').text
		block_type = soup.find('div', class_='option-group-container').get_attribute_list('class')[1] # TODO: Make sure this works.

		match block_type:
			# Game Lines
			case 'six-pack-container':
				spreads, totals, moneylines = [], [], []

				option_rows = soup.find_all('div', class_='option-row')
				for row in option_rows:
					team =  self.__get_team_abbreviation(row.find('six-pack-player-name').text)
					options = row.find_all('ms-option', class_='option')

					for option in options:
						pick = option.find('ms-event-pick', _class='option-pick')
						if pick:
							name = pick.find('div', class_='name')
							value = pick.find('div', class_='value')
							
							if name and '+' in name.text or '-' in name.text:
								line = int(name.text.replace('+', ''))
								value = int(value.text.replace('+', ''))
								spreads.append(('spread', line, value))
							elif name and 'O' in name.text or 'U' in name.text:
								ou = 'Over' if 'O' in name.text else 'Under'
								line = int(name.text.replace('O', '').replace('U', '').strip())
								value = int(value.text.replace('+', ''))
								totals.append((ou, line, value))
							else:
								moneylines.append(('moneyline', None, int(value.replace('+', ''))))
				
				six_pack_picks = itertools.chain(spreads, totals, moneylines)
				for game_line in six_pack_picks: 
					pick = self.__create_pick(event_title, self.book_name, league,
											  game_line[0], team, game_line[1], game_line[2],
											  None, None)
					block_picks.append(pick)
		
			case 'over_under_container':


				return []
			case _:
				return []
