import json
import re
from .base import SportsbookClient
from scraper.tasks import batch_upsert_odds
from common.constants.urls import ESPNBET_URLS
from common.constants.sportsbook import (
    EVENT_TTL, ODDS_TTL, PRIMARY_MARKETS,
)
from common.utils import (
    normalize_team_name, normalize_market_name, create_event_key, generate_data_hash, 
    create_market_key, utc_to_cst, format_odds, normalize_status_name, extract_float, extract_text,
)
from common.exceptions import NormalizationError

class ESPNBetClient(SportsbookClient):

    def __init__(self, league):
        super().__init__('espnbet', league)


    def parse_schedule(self):
        pass
    

    def parse_primary_odds(self, status):
        pass
    

    def parse_props(self, status):
        pass
