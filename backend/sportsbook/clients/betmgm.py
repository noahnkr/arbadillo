from datetime import datetime, timedelta, timezone

from .base import SportsbookClient

from common.utils.sportsbook_helpers import create_event_key, get_team_key
from common.exceptions import NormalizationError

class BetMGMClient(SportsbookClient):
    NAME = 'betmgm'
    SPORT_ID_MAP = {
        'baseball': 23
    }
    LEAGUE_ID_MAP = {
        'mlb': 75,
    }

    def __init__(self, sport, league):
        super().__init__(self.NAME, sport, league)

    def _get(self, url, params):
        pass
        
    def get_events(self):
        pass

    def parse_events(self):
        pass

    def get_markets(self, event_key):
        pass

    def parse_markets(self, event_key):
        pass