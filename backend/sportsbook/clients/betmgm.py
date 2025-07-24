from dateutil.parser import isoparse

from .base import SportsbookClient

from common.utils.sportsbook_helpers import create_event_key, get_team_key
from common.utils.strings import extract_float
from common.exceptions import NormalizationError

class BetMGMClient(SportsbookClient):
    NAME = 'betmgm'
    BASE_URL = 'https://www.il.betmgm.com/en/sports'
    AUTH_TOKEN = 'NWYzZTEwMDUtOGI3OS00ZGY1LTgxMGUtMWMxNjAzMWVmMGRm'
    SPORT_ID_MAP = {
        'baseball': 23
    }
    LEAGUE_ID_MAP = {
        'mlb': 75,
    }

    def __init__(self, sport, league):
        super().__init__(self.NAME, sport, league)

    def _get(self, path, intercept_query):
        url = self.BASE_URL + path
        headers = {
            'origin': 'https://ww.il.betmgm.com',
            'referer': 'https://ww.il.betmgm.com',
        }
        return super()._get(
            url,
            headers=headers,
            method='page_intercept',
            intercept_query=intercept_query
        )
        
    def get_events(self):
        league_url = f'/{self.sport}-{self.SPORT_ID_MAP[self.sport]}/betting/usa-9/{self.league}-{self.LEAGUE_ID_MAP[self.league]}'
        data = self._get(
            league_url, 
            intercept_query='fixtures'
        )

        events = data.get('fixtures', [])
        self.logger.info(f'Fetched {len(events)} events ({self.league})')
        return events

    def parse_events(self):
        events = self.get_events()
        for event in events:
            try:
                event_id = event['id']
                event_name = event['name']['value']
                clean_event_name = event_name.lower().replace('.', '').replace(' ', '-')
                event_path = f'/{clean_event_name}-{event_id}'

                participants = event_name.split(' at ')
                away_team_key = get_team_key(participants[0], self.league)
                home_team_key = get_team_key(participants[1], self.league)

                if not away_team_key or not home_team_key:
                    self.logger.warning(f'Missing team(s) aliases for {participants[0]} and/or {participants[1]} ({self.league})')
                    continue
                
                start_time = isoparse(event['startDate'])
                start_date = start_time.strftime('%Y-%m-%d')

                event_key = create_event_key(start_date, away_team_key, home_team_key)
                self.match_espn_key(event_key, event_id)
                self.redis.set(f'{self.name}:paths:{self.league}:{event_key}', event_path)

            except NormalizationError as e:
                self.logger.debug(e)
            except Exception as e:
                self.logger.exception(f'An error occured while parsing events ({self.league}): {e}')	

    def get_markets(self, event_key):
        event_id = self.redis.get(f'{self.name}:ids:{self.league}:{event_key}')
        event_path = self.redis.get(f'{self.name}:paths:{self.league}:{event_key}')
        if not event_id or not event_path:
            self.logger.warning(f'Unknown event id or event path for {event_key} ({self.league})')
            return {}
        event_url = f'/events{event_path}'
        data = self._get(
            event_url, 
            intercept_query='fixture-view'
        )

        markets = data.get('fixture', {}).get('optionMarkets', [])
        self.logger.info(f'Fetched {len(markets)} markets ({self.league})')
        return markets

    def parse_markets(self, event_key):
        market_selections = []
        markets = self.get_markets(event_key)

        for market in markets:
            market_name = market['name']['value']
            outcomes = market['options']
            for outcome in outcomes:
                try:
                    outcome_name = outcome['name']['value']
                    line = extract_float(outcome.get('attr'))
                    value = outcome['price']['odds']
                    status = outcome['status']

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
            try:
                market_name = market['name']['value']
                outcomes = market['options']
                for outcome in outcomes:
                    outcome_name = outcome['name']['value']
                    line = extract_float(outcome.get('attr'))

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
            except NormalizationError as e:
                self.logger.debug(e)
            except Exception as e:
                self.logger.exception(f'An error occured while parsing markets for {event_key} ({self.league}): {e}')
        
        return export_markets
