import json
from .base import SportsbookClient
from common.constants import DRAFTKINGS_URLS
from common.utils import (
    normalize_team_name, normalize_market_name, create_event_key, 
	current_timestamp, generate_odds_hash, create_market_key, utc_to_cst, 
	format_odds,
)
from common.playwright_manager import PlaywrightSessionManager
from common.logging import configure_logging

logger = configure_logging(__name__)

class FanDuelClient(SportsbookClient):
    name = 'fanduel'

    def __init__(self, league):
        super().__init__(league)
        self.session = PlaywrightSessionManager.get_instance()


    def parse_schedule(self):
        logger.info(f'({self.name}) starting schedule request | league={self.league}, url=')


    def parse_odds(self):
        url = 'https://sbapi.il.sportsbook.fanduel.com/api/content-managed-page?page=CUSTOM&customPageId=mlb&pbHorizontal=false&_ak=FhMFpcPWXMeyZxOx&timezone=America%2FChicago'
        logger.info(f'({self.name}) starting odds request | league={self.league}, url={url}')
        headers = {
            'origin': 'https://sportsbook.fanduel.com',
            'referer': 'https://sportsbook.fanduel.com/',
        }
        data = self.fetch_data(url, headers=headers, session=self.session)
        logger.info(data)