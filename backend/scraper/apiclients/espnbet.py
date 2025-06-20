import json
import urllib
import re

from .base import SportsbookClient

from common.utils.strings import extract_text
from common.utils.sportsbook import (
    create_event_key, create_market_key, format_odds, generate_data_hash, 
    normalize_market_name, normalize_status_name, normalize_team_name,
)
from common.constants.urls import ESPNBET_URLS, ESPNBET_AUTH_TOKEN
from common.constants.sportsbook import EVENT_TTL, ODDS_TTL, PRIMARY_MARKETS
from common.utils.time import utc_to_cst
from common.exceptions import NormalizationError
from common.utils.client import PlaywrightSessionManager

from scraper.tasks import batch_upsert_odds

class ESPNBetClient(SportsbookClient):

    def __init__(self, league):
        super().__init__('espnbet', league)
        self.session = PlaywrightSessionManager.get_instance()


    def parse_schedule(self):
        base_url = ESPNBET_URLS['base']
        league_url = ESPNBET_URLS[self.league]
        if not base_url or league_url:
            self.logger.warning(f'schedule url not found ({self.league})')
        
        self.logger.info(f'starting schedule request ({self.league})')
        try:
            headers = {
                'origin': 'https://thescore.bet',
                'referer': 'https://thescore.bet',
                'cookie': self.session.get_cookies(),
                'x-anonymous-authorization': ESPNBET_AUTH_TOKEN,
            }
            variables = {
                'canonicalUrl': league_url,
                'oddsFormat': 'AMERICAN',
                'includeRichEvent': True,
                'includeRecommendedProps': True,
                'includeSectionDefaultField': True,
                'includeTableMarketCard': True,
                'pageType': 'PAGE',
            }
            params = {
                'operationName': 'Marketplace',
                'variables': json.dumps(variables),
            }
            data = self.fetch_data(base_url, headers=headers, params=params, method='page_evaluate_fetch',  page=self.session.page)
        except Exception as e:
            self.logger.exception(f'{e} occured while yielding schedule request to {base_url} ({self.league})')
    

    def parse_primary_odds(self, status):
        pass
    

    def parse_props(self, status):
        pass
