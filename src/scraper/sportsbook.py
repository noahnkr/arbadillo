from scraper import (
    ABC, abstractmethod,
    WebDriver, datetime,
    hashlib
)

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

		Args:
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

		Args:
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
		
		Args:
			sportsbook (str): Sports book domain for the URL.
			league (str): The sports league.
			
		Returns:
				str: Base url for the league page for the given sportsbook.
		'''
		return BOOKS[self.book_name][league]
	
	@staticmethod
	def _get_team_abbreviation(team_name):
		'''
		Converts any form of team name into its 3-letter abbreviation.

		Args:
			team_name (str): The team name to convert.
			
		Returns:
			str: The 3-letter abbreviation of the team.
		'''
		return TEAM_ACRONYNMS[team_name]


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
	def _get_event_info(self, html: str) -> str:
		'''
		Gets the event information from an event page on the sports book.

		Args:
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

		Args:
			league (str): the sports league of the event.

		Returns:
			list: all available betting options for an event.
		'''
		pass

	@abstractmethod
	def _scrape_block(self, block, league, event_title) -> str:
		pass


BOOKS = {
	'Caesars': {
		'NBA': 'https://sportsbook.caesars.com/us/il/bet/basketball/events/'
	},
	'DraftKings': {},
	'BetMGM': {
		'NBA': 'https://sports.il.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004',
        'MLB': 'https://sports.il.betmgm.com/en/sports/baseball-23/betting/usa-9/mlb-75'
	},
	'BetRivers': {},
	'PointsBet': {},
	'ESPNBet': {}
}

PROPS = {
	'Caesars': {},
	'DraftKings': {},
	'BetMGM': {
    'MLB': {
			# Batting
      'HITS', 'RBIS', 'BASES', 'H+R+RBI', 'STOLEN BASES', 'TOTAL RUNS', 'SINGLES', 'DOUBLES', 'TRIPLES', 'WALKS',
			# Pitching
			'STRIKEOUTS', 'PITCHER HITS ALLOWED', 'EARNED RUNS', 'OUTS',
		},
	},
	'BetRivers': {},
	'PointsBet': {},
	'ESPNBet': {}
}

TEAM_ACRONYNMS = {
	# NBA
	'ATLANTA HAWKS': 'ATL', 'ATLANTA': 'ATL', 'HAWKS': 'ATL', 'ATL': 'ATL',
	'BOSTON CELTICS': 'BOS', 'BOSTON': 'BOS', 'CELTICS': 'BOS', 'BOS': 'BOS',
	'BROOKLYN NETS': 'BKN', 'BROOKLYN':'BKN', 'NETS': 'BKN', 'BKN': 'BKN',
	'CHARLOTTE HORNETS': 'CHA', 'CHARLOTTE': 'CHA', 'HORNETS': 'CHA', 'CHA': 'CHA',
	'CHICAGO BULLS': 'CHI', 'CHICAGO': 'CHI', 'BULLS': 'CHI', 'CHI': 'CHI',
	'CLEVELAND CAVALIERS': 'CLE', 'CLEVELAND': 'CLE', 'CAVALIERS': 'CLE', 'CLE': 'CLE',
	'DALLAS MAVERICKS': 'DAL', 'DALLAS': 'DAL', 'MAVERICKS': 'DAL', 'DAL': 'DAL',
	'DENVER NUGGETS': 'DEN', 'DENVER': 'DEN', 'NUGGETS': 'DEN', 'DEN': 'DEN',
	'DETROIT PISTONS': 'DET', 'DETROIT': 'DET', 'PISTONS': 'DET', 'DET': 'DET',
	'GOLDEN STATE WARRIORS': 'GSW', 'GOLDEN STATE': 'GSW', 'WARRIORS': 'GSW', 'GSW': 'GSW',
	'HOUSTON ROCKETS': 'HOU', 'HOUSTON': 'HOU', 'ROCKETS': 'HOU', 'HOU': 'HOU',
	'INDIANA PACERS': 'IND', 'INDIANA': 'IND', 'PACERS': 'IND', 'IND': 'IND',
	'LOS ANGELES CLIPPERS': 'LAC', 'LA': 'LAC', 'CLIPPERS': 'LAC', 'LAC': 'LAC',
	'LOS ANGELES LAKERS': 'LAL', 'LOS ANGELES': 'LAL', 'LAKERS': 'LAL', 'LAL': 'LAL',
	'MEMPHIS GRIZZLIES': 'MEM', 'MEMPHIS': 'MEM', 'GRIZZLIES': 'MEM', 'MEM': 'MEM',
	'MIAMI HEAT': 'MIA', 'MIAMI': 'MIA', 'HEAT': 'MIA', 'MIA': 'MIA',
	'MILWAUKEE BUCKS': 'MIL', 'MILWAUKEE': 'MIL', 'BUCKS': 'MIL', 'MIL': 'MIL',
	'MINNESOTA TIMBERWOLVES': 'MIN', 'MINNESOTA': 'MIN', 'TIMBERWOLVES': 'MIN', 'MIN': 'MIN',
	'NEW ORLEANS PELICANS': 'NOP', 'NEW ORLEANS': 'NOP', 'PELICANS': 'NOP', 'NOP': 'NOP',
	'NEW YORK KNICKS': 'NYK', 'NEW YORK': 'NYK', 'KNICKS': 'NYK', 'NYK': 'NYK',
	'OKLAHOMA CITY THUNDER': 'OKC', 'OKLAHOMA CITY': 'OKC', 'THUNDER': 'OKC', 'OKC': 'OKC',
	'ORLANDO MAGIC': 'ORL', 'ORLANDO': 'ORL', 'MAGIC': 'ORL', 'ORL': 'ORL',
	'PHILADELPHIA 76ERS': 'PHI', 'PHILADELPHIA': 'PHI', '76ERS': 'PHI', 'PHI': 'PHI',
	'PHOENIX SUNS': 'PHX', 'PHOENIX': 'PHX', 'SUNS': 'PHX', 'PHX': 'PHX',
	'PORTLAND TRAIL BLAZERS': 'POR', 'PORTLAND TRAILBLAZERS': 'POR', 'PORTLAND': 'POR', 'TRAIL BLAZERS': 'POR', 'TRAILBLAZERS': 'POR', 'POR': 'POR',
	'SACRAMENTO KINGS': 'SAC', 'SACRAMENTO': 'SAC', 'KINGS': 'SAC', 'SAC': 'SAC',
	'SAN ANTONIO SPURS': 'SAS', 'SAN ANTONIO': 'SAS', 'SPURS': 'SAS', 'SAS': 'SAS',
	'TORONTO RAPTORS': 'TOR', 'TORONTO': 'TOR', 'RAPTORS': 'TOR', 'TOR': 'TOR',
	'UTAH JAZZ': 'UTA', 'UTAH': 'UTA', 'JAZZ': 'UTA', 'UTA': 'UTA',
	'WASHINGTON WIZARDS': 'WAS', 'WASHINGTON': 'WAS', 'WIZARDS': 'WAS', 'WAS': 'WAS',

	# NFL
	'ARIZONA CARDINALS': 'ARI', 'ARIZONA': 'ARI', 'CARDINALS': 'ARI', 'ARI': 'ARI',
	'ATLANTA FALCONS': 'ATL', 'ATLANTA': 'ATL', 'FALCONS': 'ATL', 'ATL': 'ATL',
	'BALTIMORE RAVENS': 'BAL', 'BALTIMORE': 'BAL', 'RAVENS': 'BAL', 'BAL': 'BAL',
	'BUFFALO BILLS': 'BUF', 'BUFFALO': 'BUF', 'BILLS': 'BUF', 'BUF': 'BUF',
	'CAROLINA PANTHERS': 'CAR', 'CAROLINA': 'CAR', 'PANTHERS': 'CAR', 'CAR': 'CAR',
	'CHICAGO BEARS': 'CHI', 'CHICAGO': 'CHI', 'BEARS': 'CHI', 'CHI': 'CHI',
	'CINCINNATI BENGALS': 'CIN', 'CINCINNATI': 'CIN', 'BENGALS': 'CIN', 'CIN': 'CIN',
	'CLEVELAND BROWNS': 'CLE', 'CLEVELAND': 'CLE', 'BROWNS': 'CLE', 'CLE': 'CLE',
	'DALLAS COWBOYS': 'DAL', 'DALLAS': 'DAL', 'COWBOYS': 'DAL', 'DAL': 'DAL',
	'DENVER BRONCOS': 'DEN', 'DENVER': 'DEN', 'BRONCOS': 'DEN', 'DEN': 'DEN',
	'DETROIT LIONS': 'DET', 'DETROIT': 'DET', 'LIONS': 'DET', 'DET': 'DET',
	'GREEN BAY PACKERS': 'GB', 'GREEN BAY': 'GB', 'PACKERS': 'GB', 'GB': 'GB',
	'HOUSTON TEXANS': 'HOU', 'HOUSTON': 'HOU', 'TEXANS': 'HOU', 'HOU': 'HOU',
	'INDIANAPOLIS COLTS': 'IND', 'INDIANAPOLIS': 'IND', 'COLTS': 'IND', 'IND': 'IND',
	'JACKSONVILLE JAGUARS': 'JAX', 'JACKSONVILLE': 'JAX', 'JAGUARS': 'JAX', 'JAX': 'JAX',
	'KANSAS CITY CHIEFS': 'KC', 'KANSAS CITY': 'KC', 'CHIEFS': 'KC', 'KC': 'KC',
	'LOS ANGELES CHARGERS': 'LAC', 'LOS ANGELES C': 'LAC', 'CHARGERS': 'LAC', 'LAC': 'LAC',
	'LOS ANGELES RAMS': 'LAR', 'LOS ANGELES R': 'LAR', 'RAMS': 'LAR', 'LAR': 'LAR',
	'MIAMI DOLPHINS': 'MIA', 'MIAMI': 'MIA', 'DOLPHINS': 'MIA', 'MIA': 'MIA',
	'MINNESOTA VIKINGS': 'MIN', 'MINNESOTA': 'MIN', 'VIKINGS': 'MIN', 'MIN': 'MIN',
	'NEW ENGLAND PATRIOTS': 'NE', 'NEW ENGLAND': 'NE', 'PATRIOTS': 'NE', 'NE': 'NE',
	'NEW ORLEANS SAINTS': 'NO', 'NEW ORLEANS': 'NO', 'SAINTS': 'NO', 'NO': 'NO',
	'NEW YORK GIANTS': 'NYG', 'NEW YORK G': 'NYG', 'GIANTS': 'NYG', 'NYG': 'NYG',
	'NEW YORK JETS': 'NYJ', 'NEW YORK J': 'NYJ', 'JETS': 'NYJ', 'NYJ': 'NYJ',
	'LAS VEGAS RAIDERS': 'LV', 'LAS VEGAS': 'LV', 'RAIDERS': 'LV', 'LV': 'LV',
	'PHILADELPHIA EAGLES': 'PHI', 'PHILADELPHIA': 'PHI', 'EAGLES': 'PHI', 'PHI': 'PHI',
	'PITTSBURGH STEELERS': 'PIT', 'PITTSBURGH': 'PIT', 'STEELERS': 'PIT', 'PIT': 'PIT',
	'SAN FRANCISCO 49ERS': 'SF', 'SAN FRANCISCO': 'SF', '49ERS': 'SF', 'SF': 'SF',
	'SEATTLE SEAHAWKS': 'SEA', 'SEATTLE': 'SEA', 'SEAHAWKS': 'SEA', 'SEA': 'SEA',
	'TAMPA BAY BUCCANEERS': 'TB', 'TAMPA BAY': 'TB', 'BUCCANEERS': 'TB', 'TB': 'TB',
	'TENNESSEE TITANS': 'TEN', 'TENNESSEE': 'TEN', 'TITANS': 'TEN', 'TEN': 'TEN',
	'WASHINGTON FOOTBALL TEAM': 'WAS', 'WASHINGTON': 'WAS', 'WFT': 'WAS', 'WAS': 'WAS',

	# MLB
	'ARIZONA DIAMONDBACKS': 'ARI', 'ARIZONA': 'ARI', 'DIAMONDBACKS': 'ARI', 'ARI': 'ARI',
	'ATLANTA BRAVES': 'ATL', 'ATLANTA': 'ATL', 'BRAVES': 'ATL', 'ATL': 'ATL',
	'BALTIMORE ORIOLES': 'BAL', 'BALTIMORE': 'BAL', 'ORIOLES': 'BAL', 'BAL': 'BAL',
	'BOSTON RED SOX': 'BOS', 'BOSTON': 'BOS', 'RED SOX': 'BOS', 'BOS': 'BOS',
	'CHICAGO WHITE SOX': 'CWS', 'CHICAGO W': 'CWS', 'WHITE SOX': 'CWS', 'CWS': 'CWS',
	'CHICAGO CUBS': 'CHC', 'CHICAGO C': 'CHC', 'CUBS': 'CHC', 'CHC': 'CHC',
	'CINCINNATI REDS': 'CIN', 'CINCINNATI': 'CIN', 'REDS': 'CIN', 'CIN': 'CIN',
	'CLEVELAND GUARDIANS': 'CLE', 'CLEVELAND': 'CLE', 'GUARDIANS': 'CLE', 'CLE': 'CLE',
	'COLORADO ROCKIES': 'COL', 'COLORADO': 'COL', 'ROCKIES': 'COL', 'COL': 'COL',
	'DETROIT TIGERS': 'DET', 'DETROIT': 'DET', 'TIGERS': 'DET', 'DET': 'DET',
	'HOUSTON ASTROS': 'HOU', 'HOUSTON': 'HOU', 'ASTROS': 'HOU', 'HOU': 'HOU',
	'KANSAS CITY ROYALS': 'KC', 'KANSAS CITY': 'KC', 'ROYALS': 'KC', 'KC': 'KC',
	'LOS ANGELES ANGELS': 'LAA', 'LA ANGELS': 'LAA', 'ANGELS': 'LAA', 'LAA': 'LAA',
	'LOS ANGELES DODGERS': 'LAD', 'LA DODGERS': 'LAD', 'DODGERS': 'LAD', 'LAD': 'LAD',
	'MIAMI MARLINS': 'MIA', 'MIAMI': 'MIA', 'MARLINS': 'MIA', 'MIA': 'MIA',
	'MILWAUKEE BREWERS': 'MIL', 'MILWAUKEE': 'MIL', 'BREWERS': 'MIL', 'MIL': 'MIL',
	'MINNESOTA TWINS': 'MIN', 'MINNESOTA': 'MIN', 'TWINS': 'MIN', 'MIN': 'MIN',
	'NEW YORK METS': 'NYM', 'NEW YORK M': 'NYM', 'METS': 'NYM', 'NYM': 'NYM',
	'NEW YORK YANKEES': 'NYY', 'NEW YORK Y': 'NYY', 'YANKEES': 'NYY', 'NYY': 'NYY',
	'OAKLAND ATHLETICS': 'OAK', 'OAKLAND': 'OAK', 'ATHLETICS': 'OAK', 'OAK': 'OAK',
	'PHILADELPHIA PHILLIES': 'PHI', 'PHILADELPHIA': 'PHI', 'PHILLIES': 'PHI', 'PHI': 'PHI',
	'PITTSBURGH PIRATES': 'PIT', 'PITTSBURGH': 'PIT', 'PIRATES': 'PIT', 'PIT': 'PIT',
	'SAN DIEGO PADRES': 'SD', 'SAN DIEGO': 'SD', 'PADRES': 'SD', 'SD': 'SD',
	'SAN FRANCISCO GIANTS': 'SF', 'SAN FRANCISCO': 'SF', 'GIANTS': 'SF', 'SF': 'SF',
	'SEATTLE MARINERS': 'SEA', 'SEATTLE': 'SEA', 'MARINERS': 'SEA', 'SEA': 'SEA',
	'ST. LOUIS CARDINALS': 'STL', 'ST LOUIS': 'STL', 'CARDINALS': 'STL', 'STL': 'STL',
	'TAMPA BAY RAYS': 'TB', 'TAMPA BAY': 'TB', 'RAYS': 'TB', 'TB': 'TB',
	'TEXAS RANGERS': 'TEX', 'TEXAS': 'TEX', 'RANGERS': 'TEX', 'TEX': 'TEX',
	'TORONTO BLUE JAYS': 'TOR', 'TORONTO': 'TOR', 'BLUE JAYS': 'TOR', 'TOR': 'TOR',
	'WASHINGTON NATIONALS': 'WAS', 'WASHINGTON': 'WAS', 'NATIONALS': 'WAS', 'WAS': 'WAS',
}