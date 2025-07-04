import re

from dateutil.parser import isoparse

from .base import SportsbookClient

from common.utils.sportsbook_helpers import create_event_key, get_team_key
from common.exceptions import NormalizationError

class FanDuelClient(SportsbookClient):
    NAME = 'fanduel'
    BASE_URL = 'https://sbapi.il.sportsbook.fanduel.com/api'
    AUTH_TOKEN = 'FhMFpcPWXMeyZxOx'

    def __init__(self, sport: str, league: str):
        super().__init__(self.NAME, sport, league)
    
    def _get(self, path, params):
        url = self.BASE_URL + path
        headers = {
            'origin': 'https://sportsbook.fanduel.com',
            'referer': 'https://sportsbook.fanduel.com',
        }
        params.extend([
            ('_ak', self.AUTH_TOKEN),
            ('timezone', 'America%2FChicago'),
        ])
        return super()._get(url, headers=headers, params=params).get('attachments', {})
    
    def get_events(self):
        league_url = '/content-managed-page'
        params = [
            ('page', 'CUSTOM'),
            ('customPageId', self.league),
        ]
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
                if len(teams) != 2:
                    continue

                away_team = teams[0].strip()
                home_team = teams[1].strip()
                away_team_key = get_team_key(away_team, self.league)
                home_team_key = get_team_key(home_team, self.league)

                if not away_team_key or not home_team_key:
                    self.logger.warning(f'Missing team(s) aliases for {away_team} and/or {home_team} ({self.league})')
                    continue

                start_time = isoparse(event['openDate'])
                start_date = start_time.strftime('%Y-%m-%d')

                event_key = create_event_key(start_date, away_team_key, home_team_key)
                self.match_espn_key(event_key, event_id)

            except NormalizationError as e:
                self.logger.debug(e)
            except Exception as e:
                self.logger.exception(f'An error occured while parsing events ({self.league}): {e}')
    
    def get_markets(self, event_key):
        event_id = self.redis.get(f'{self.name}:ids:{self.league}:{event_key}')
        if not event_id:
            self.logger.warning(f'Unknown event id for {event_key} ({self.league})')
            return []

        event_status = 'upcoming' if self.redis.sismember(f'events:{self.league}:upcoming', event_key) else 'active'

        event_url = '/event-page'
        params = [
            ('eventId', event_id),
            ('tab', 'same-game-parlay-' if event_status == 'upcoming' else 'live-sgp'),
        ]

        markets = self._get(event_url, params=params).get('markets', {}).values()
        self.logger.info(f'Fetched {len(markets)} markets for {event_key} ({self.league})')
        return markets

    def parse_markets(self, event_key):
        market_selections = []

        markets = self.get_markets(event_key)
        for market in markets:
            market_name = market['marketName']

            selections = market['runners']
            for selection in selections:
                try:
                    outcome_name = selection['runnerName']
                    line = selection['handicap'] if selection['handicap'] else None
                    value = selection.get('winRunnerOdds', {}).get('trueOdds', {}).get('decimalOdds', {}).get('decimalOdds', 0)
                    status = selection['runnerStatus'] if value else 'suspended'

                    selection_data = self.parse_selection(
                        event_key, 
                        market_name, 
                        outcome_name,
                        value=value,
                        line=line, 
                        status=status
                    )
                    if self.compare_and_update_selection(selection_data):
                        market_selections.append(selection_data)

                except NormalizationError as e:
                    self.logger.debug(e)
                except Exception as e:
                    self.logger.exception(f'An error occured while parsing markets for {event_key} ({self.league}): {e}')

        return market_selections

    def export_markets(self, event_key):
        export_markets = []

        markets = self.get_markets(event_key)
        for market in markets:
            market_name = market['marketName']

            selections = market['runners']
            for selection in selections:
                try:
                    outcome_name = selection['runnerName']
                    line = selection['handicap'] if selection['handicap'] else None

                    export_selection = {
                        'market_name': market_name,
                        'outcome_name': outcome_name,
                        'line': line,
                        'team': None,
                        'player': None,
                        'expected': None,
                        'expected_exception': None
                    }

                    try:
                        selection_data = self.parse_selection(
                            event_key, 
                            market_name, 
                            outcome_name,
                            line=line, 
                        ).to_dict()

                        for key in ['sportsbook', 'league', 'event_key', 'market_key', 'status', 'value', 'collected_at']:
                            selection_data.pop(key, None)

                        export_selection['expected'] = selection_data
                        export_selection['expected_exception'] = False
                    except NormalizationError:
                        export_selection['expected_exception'] = True

                    export_markets.append(export_selection)

                except Exception as e:
                    self.logger.exception(f'An error occured while parsing markets for {event_key} ({self.league}): {e}')

        return export_markets