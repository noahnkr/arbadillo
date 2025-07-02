from dateutil.parser import isoparse

from .base import SportsbookClient

from common.utils.sportsbook_helpers import create_event_key, get_team_key
from common.exceptions import NormalizationError

class BetRiversClient(SportsbookClient):
    NAME = 'betrivers'
    BASE_URL = 'https://il.betrivers.com/api/service/sportsbook/offering/listview'
    LEAGUE_ID_MAP = {
        'mlb': 1000093616,
    }
    CAGE_CODE = 847

    def __init__(self, sport, league):
        super().__init__(self.NAME, sport, league)

    def _get(self, path, params):
        url = self.BASE_URL + path
        headers = {
            'origin': 'https://betrivers.com',
            'referer': 'https://betrivers.com'
        }
        return super()._get(url, headers=headers, params=params)

    def get_events(self):
        league_url = '/events'
        params = {
            'type': 'live',
            'type': 'prematch',
            'cageCode': self.CAGE_CODE,
            'groupId': self.LEAGUE_ID_MAP[self.league],
        }
        data = self._get(league_url, params)

        events = data.get('items', [])
        self.logger.info(f'Fetched {len(events)} events ({self.league})')

        return events

    def parse_events(self):
        events = self.get_events()
        for event in events:
            try:
                event_id = event['id']

                participants = event['participants']
                away_team = participants[0]['name'] if not participants[0]['home'] else participants[1]['name']
                home_team = participants[0]['name'] if participants[0]['home'] else participants[1]['name']
                away_team_key = get_team_key(away_team, self.league)
                home_team_key = get_team_key(home_team, self.league)

                if not away_team_key or not home_team_key:
                    self.logger.warning(f'Missing team(s) aliases for {away_team} and/or {home_team} ({self.league})')
                    continue
                    
                start_time = isoparse(event['start'])
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
            return {}
        event_url = '/details'
        params = {
            'eventId': event_id,
            'cageCode': self.CAGE_CODE,
        }
        data = self._get(event_url, params)

        markets = [market for category in data.get('offeringGroups', []) for market in category['criterionGroups']]
        self.logger.info(f'Fetched {len(markets)} markets ({self.league})')
        return markets

    def parse_markets(self, event_key):
        market_selections = []

        markets = self.get_markets(event_key)
        for market in markets:
            try:
                market_name = market['criterionName']
                selections = market['betOffers']
                for selection in selections:
                    outcomes = selection['outcomes']
                    for outcome in outcomes:
                        outcome_name = outcome['label']
                        line = outcome.get('line')
                        value = outcome['odds']
                        status = outcome['status']

                        team, player = None, None
                        participant = outcome.get('participantName')
                        if participant:
                            last, first = participant.split(',')
                            player = f'{first.strip()} {last.strip()}'

                        selection_data = self.parse_selection(
                            event_key,
                            market_name,
                            outcome_name,
                            value=value,
                            line=line,
                            team=team,
                            player=player,
                            status=status,
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
                market_name = market['criterionName']
                selections = market['betOffers']
                for selection in selections:
                    outcomes = selection['outcomes']
                    for outcome in outcomes:
                        outcome_name = outcome['label']
                        line = outcome.get('line')

                        team, player = None, None
                        participant = outcome.get('participant')
                        if participant:
                            try:
                                get_team_key(participant, self.league)
                                team = participant
                            except NormalizationError:
                                last, first = participant.split(',')
                                player = f'{first.strip()} {last.strip()}'


                        export_selection = {
                            'market_name': market_name,
                            'outcome_name': outcome_name,
                            'line': line,
                            'team': team,
                            'player': player,
                            'expected': None,
                            'expected_exception': None
                        }

                        try:
                            selection_data = self.parse_selection(
                                event_key,
                                market_name,
                                outcome_name,
                                line=line,
                                team=team,
                                player=player,

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