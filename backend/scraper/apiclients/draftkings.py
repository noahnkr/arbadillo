import requests
from .base import SportsbookClient
from common.constants import SPORTSBOOK_URLS
from common.logging import configure_logging

logger = configure_logging(__name__)

class DraftKingsClient(SportsbookClient):
	name = 'draftkings'

	def __init__(self, league=None):
		super().__init__(league)

	
	def parse_schedule(self):
		logger.info(f'({self.name}) parsing schedule | league={self.league}')
		url = SPORTSBOOK_URLS[self.name][self.league]
		if url:
			headers = {
				'Accept': 'application/json',
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
			}
			res = requests.get(url, headers=headers)

			if res.ok:
				logger.info(f'({self.name}) success!')
			else:
				logger.info(f'({self.name}) failed....')
		
		
	def parse_odds(self):
		logger.info(f'({self.name}) parsing odds | league={self.league}')