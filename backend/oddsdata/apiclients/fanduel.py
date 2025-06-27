import re
import json

from .base import SportsbookClient

from common.utils.sportsbook import (
    create_event_key, create_market_key, normalize_market_name, normalize_status_name, normalize_team_name,
    correct_over_under_line, normalize_market_outcome, format_odds
)
from common.utils.time import utc_to_cst
from common.exceptions import NormalizationError
from common.utils.client import PlaywrightSessionManager

class FanDuelClient(SportsbookClient):
    BASE_URL = 'https://sbapi.il.sportsbook.fanduel.com/api'
    AUTH_TOKEN = 'FhMFpcPWXMeyZxOx'

    def __init__(self, sport: str, league: str):
        super().__init__('fanduel', sport, league)
        self.session = PlaywrightSessionManager.get_instance()
    
    def _get(self, path, params):
        url = self.BASE_URL + path
        headers = {
            'origin': 'https://sportsbook.fanduel.com',
            'referer': 'https://sportsbook.fanduel.com',
        }
        final_params = {
            '_ak': self.AUTH_TOKEN,
            'timezone': 'America%2FChicago',
            **params
        }
        return super()._get(
            url, headers=headers, params=final_params, method='playwright_request', context=self.session.context
        ).get('attachments', {})
    
    def get_events(self):
        league_url = f'/content-managed-page'
        params = {
            'page': 'CUSTOM',
            'customPageId': self.league,
        }
        data = self._get(league_url, params=params)

        events = data.get('events', {}).values()
        self.logger.info(f'Fetched {len(events)} events ({self.league})')
        return events

    def parse_events(self):
        events = self.get_events()
        for event in events:
            try:
                event_id = event['eventId']

                clean_name = re.sub(r'\s*\([^)]*\)', '', event['name']) # Remove primary player name inside parenthesis 
                teams = clean_name.split('@')
                away_team = teams[0].strip()
                home_team = teams[1].strip()
                away_team_key = self.redis.get(f'events:aliases:{self.league}:{away_team}')
                home_team_key = self.redis.get(f'events:aliases:{self.league}:{home_team}')

                if not away_team_key or not home_team_key:
                    self.logger.warning(f'Missing team(s) aliases for {away_team} and/or {home_team} ({self.league})')
                    continue

                start_time = utc_to_cst(event['openDate'])
                start_date = start_time.split('T')[0]

                event_key = create_event_key(self.league, start_date, away_team_key, home_team_key)
                self.match_espn_key(event_key, event_id)
            except Exception as e:
                self.logger.exception(f'An error occured while parsing events ({self.league}): {e}')
    
    def get_markets(self, event_key):
        event_id = self.redis.get(f'{self.name}:ids:{event_key}')
        if not event_id:
            self.logger.warning(f'Unknown event id for {event_key} ({self.league})')
            return []

        event_status = 'upcoming' if self.redis.sismember(f'events:{self.league}:upcoming') else 'active'

        event_url = f'/event-page'
        params = {
            'eventId': event_id,
            'tab': 'same-game-parlay-' if event_status == 'upcoming' else 'live-sgp'
        }

        markets = self._get(event_url, params=params).get('markets', {})
        self.logger.info(f'Fetched {len(markets)} markets for {event_key} ({self.league})')
        return markets

    def parse_markets(self, event_key):
        odds = []
        markets = self.get_markets(event_key)
        for market in markets:
            market_name = market['marketName']
            selections = market['runners']
            for selection in selections:
                try:
                    outcome_name = selection['runnerName']
                    line = selection['handicap'] if selection['handicap'] else None
                    value = selection['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds']
                    status = selection['runnerStatus']

                    odds_data =  self.parse_selection(event_key, market_name, outcome_name, line=line, value=value, status=status)
                    if self.compare_and_update_odds_cache(odds_data):
                        odds.append(odds_data)

                except Exception as e:
                    self.logger.exception(f'An error occured while parsing markets for {event_key} ({self.league}): {e}')

        return odds