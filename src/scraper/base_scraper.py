from . import *

class BaseScraper(ABC):
	def __init__(self, driver: WebDriver, book_name: str):
		self.driver = driver
		self.book_name = book_name
		self.wait = WebDriverWait(self.driver, 10)


	# TODO: Add more querying
	def scrape(self, leagues: list) -> list:
		'''
		Get's all the picks and their odds for this sports book in the given leagues.

		Navigates a sports book and for each league, starting from the league's base URL,
		scrapes a list of every possible picks and it's odds for each event happening in 
		the requested leagues.

		Args:
			leagues (list): a list of the desired leagues to get odds data from.

		Returns:
			list: sportsbook odds
		'''
		picks = []
		for league in leagues:
			try:
				if league not in LEAGUES:
					raise InputError(f'League `{league} not supported`')
				league_picks = self._scrape_league(league)
				picks.extend(league_picks)
			except ScraperError as e:
				print(f'Error getting picks for league {league}: {e}')
			except Exception as e:
				print(f'Unexpected error for league {league}: {e}')

		self.driver.close()
		return picks


	@staticmethod
	def _create_pick(event: str, book: str, league: str, pick_type: str,
					 team: str, line: float, odds: int, player: str, prop: str) -> dict:
		'''
        Creates a pick dictionary with a unique hash based on the input parameters.

        A pick refers to an available betting option across sportsbooks. 
        The `pick_hash` field helps identify if different picks from different sportsbooks 
        are referring to the same betting option.

        Args:
            event (str): The title of the sporting event.
            book (str): The name of the sportsbook.
            league (str): The league associated with the event.
            pick_type (str): The type of pick (e.g., spread, moneyline, total).
            team (str): The team associated with the pick.
            line (float): The betting line for the pick.
            odds (int): The odds associated with the pick.
            player (str): The player associated with the pick, if any.
            prop (str): The prop bet associated with the pick, if any.

        Returns:
            dict: A dictionary containing the pick details, including:
                - pick_hash (str): A SHA-256 hash generated from the input parameters.
                - event (str): The title of the sporting event.
                - book (str): The name of the sportsbook.
                - league (str): The league associated with the event.
                - type (str): The type of pick.
                - team (str): The team associated with the pick.
                - line (float): The betting line for the pick.
                - odds (int): The odds associated with the pick.
                - player (str): The player associated with the pick, if any.
                - prop (str): The prop bet associated with the pick, if any.
                - timestamp (str): The current datetime when the pick was created, in ISO 8601 format.

        Note:
            The `pick_hash` is generated using a SHA-256 hash of a string formed by concatenating
            the input parameters with underscores. This helps in identifying if different picks
            from different sportsbooks refer to the same betting option.
        '''
		pick_values = [event, league, pick_type,
					   team, line, odds, player, prop]

		pick_string = '_'.join(str(p) if p is not None else '' for p in pick_values)
		pick_hash = hashlib.sha256(pick_string.encode()).hexdigest()
		timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

		return {
			'pick_hash': pick_hash,
			'event': event,
			'book': book,
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
        Retrieves the base URL for the specified league from the stored book's base URLs.

        This method uses the `book_name` attribute of the instance to look up the base URL
        for the given league in the `BOOK_BASE_URL` dictionary.

        Args:
            league (str): The league for which to retrieve the base URL.

        Returns:
            str: The base URL associated with the specified league for the current sportsbook.

        Raises:
            KeyError: If the book name or league does not exist in the `BOOK_BASE_URL` dictionary.

        Example:
            If `self.book_name` is "ExampleBook" and the `league` is "NFL", the method will look up
            `BOOK_BASE_URL["ExampleBook"]["NFL"]` and return the corresponding URL.

        Note:
            Ensure that the `BOOK_BASE_URL` dictionary is properly populated with the base URLs
            for all supported books and leagues.
        '''
		return BOOK_BASE_URL[self.book_name][league]
	
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
	def _format_event_datetime(self, date: str, time: str) -> str:
		'''
		Converts a date in a specific format according to the sportsbook
		into the general format YYYY-MM-DD.

		Args:
			date (str): event date.
			time (str): event time.
		
		Returns:
			str: formatted date in the format YYYY-MM-DD.
		'''
		pass


	@abstractmethod
	def _get_event_info(self, soup: BeautifulSoup) -> str:
		'''
		Gets the event information from an event page on the sports book.

		Args:
			soup (BeautifulSoup): parsed HTML content of the event page

		Returns:
			tuple: Away, Home, Datetime
		'''
		pass


	@abstractmethod
	def _scrape_league(self, league: str) -> list:
		'''Scrapes all the possible picks and their odds for the league on this sports book.'''
		pass
		 

	@abstractmethod
	def _scrape_event(self, league: str, picks: list) -> None:
		'''
		Scrapes an event page for a certain sports book. 

		This function scrapes all of the available game and player prop odds
		for this event, and stores the data in a list.

		Args:
			league (str): the sports league of the event.

		Returns:
			list: all available betting options for an event.
		'''
		pass

	@abstractmethod
	def _scrape_block(self, block: WebElement, league: str, event: str, picks: list) -> None:
		pass
