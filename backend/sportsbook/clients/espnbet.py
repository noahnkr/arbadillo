import json
import os

from dateutil.parser import isoparse

from .base import SportsbookClient

from common.utils.sportsbook_helpers import create_event_key, get_team_key
from common.exceptions import NormalizationError

class ESPNBetClient(SportsbookClient):
    NAME = 'espnbet'
    BASE_URL = 'https://sportsbook-tsb.ca-default.thescore.bet/graphql/persisted_queries/a10930c7eba26a588efb729298364a07aa4cdcd40d456dd061dee1355bfb8e86'

    def __init__(self, sport: str, league: str):
        super().__init__(self.NAME, sport, league)
        self.AUTH_TOKEN = os.getenv('ESPNBET_AUTH_TOKEN', '')
        if not self.AUTH_TOKEN:
            raise ValueError('ESPNBET_AUTH_TOKEN environment variable is not set')

    def _get(self, path):
        headers = {
            'origin': 'https://thescore.bet',
            'referer': 'https://thescore.bet',
            'x-anonymous-authorization': self.AUTH_TOKEN,
        }
        variables = {
            'canonicalUrl': path,
            'oddsFormat': 'AMERICAN',
            'includeRichEvent': True,
            'includeRecommendedProps': True,
            'includeSectionDefaultField': True,
            'includeTableMarketCard': True,
            'pageType': 'PAGE',
        }
        params = [
            ('operationName', 'Marketplace'),
            ('variables', json.dumps(variables)),
        ]
        return super()._get(
            self.BASE_URL, 
            headers=headers, 
            params=params, 
            method='page_evaluate_fetch',
        ).get('data', {}).get('page', {}).get('defaultChild', {})

    def get_events(self):
        league_url = f'/sport/{self.sport}/organization/united-states/competition/{self.league}'
        data = self._get(league_url)
        events_section = next(
            (s for s in data.get('sectionChildren', {}) if s.get('__typename', '') == 'MarketplaceShelf'),
            None
        )
        if not events_section:
            self.logger.warning(f'Unable to locate events section ({self.league})')
            return []
        
        events = events_section.get('marketplaceShelfChildren', [])
        self.logger.info(f'Fetched {len(events)} events ({self.league})')

        return events

    def parse_events(self):
        events = self.get_events()
        for event in events:
            try:
                event_data = event['fallbackEvent']
                event_id = event_data['id'].split(':')[1]

                away_team = event_data['awayParticipant']['fullName']
                home_team = event_data['homeParticipant']['fullName']
                away_team_key = get_team_key(away_team, self.league)
                home_team_key = get_team_key(home_team, self.league)

                if not away_team_key or not home_team_key:
                    self.logger.warning(f'Missing team(s) aliases for {away_team} and/or {home_team} ({self.league})')
                    continue

                start_time = isoparse(event_data['startTime'])
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

        event_url = f'/sport/{self.sport}/organization/united-states/competition/{self.league}/event/{event_id}'
        data = self._get(event_url)

        if not data:
            self.logger.warning(f'No data recieved for {event_key} ({self.league})')

        markets = data.get('sectionChildren', [])
        self.logger.info(f'fetched {len(markets)} markets for {event_key} ({self.league})')
        return markets

    def parse_markets(self, event_key):
        market_selections = []
        
        markets = self.get_markets(event_key)
        for market in markets:
            market_name = market['labelText']
            market_children = market['drawerChildren'][0].get('marketplaceShelfChildren', [])
            for market_child in market_children if market_children else []:
                player_container = market_child.get('participant', {})
                player = player_container.get('fullName') if player_container else None

                sub_markets = market_child.get('markets', [])
                for sub_market in sub_markets:
                    selections = sub_market.get('selections', [])
                    for selection in selections:
                        outcome_name = selection['name']['cleanName']

                        line = (selection.get('points') or {}).get('decimalPoints')
                        team = (selection.get('participant') or {}).get('fullName')

                        if not selection.get('odds'):
                            value = 0
                            status = 'suspended'
                        else:
                            value = selection['odds']['numerator'] / selection['odds']['denominator']
                            status = 'active'

                        try:
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
            market_name = market['labelText']
            market_children = market['drawerChildren'][0].get('marketplaceShelfChildren', [])
            for market_child in market_children if market_children else []:
                player_container = market_child.get('participant', {})
                player = player_container.get('fullName') if player_container else None

                sub_markets = market_child.get('markets', [])
                for sub_market in sub_markets:
                    selections = sub_market.get('selections', [])
                    for selection in selections:
                        outcome_name = selection['name']['cleanName']

                        line = (selection.get('points') or {}).get('decimalPoints')
                        team = (selection.get('participant') or {}).get('fullName')

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
                        except Exception:
                            continue
                        
                        export_markets.append(export_selection)

        return export_markets