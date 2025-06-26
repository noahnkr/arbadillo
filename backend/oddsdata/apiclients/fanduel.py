import re
import json

from .base import OddsClient

from common.utils.sportsbook import (
    create_event_key, create_market_key, normalize_market_name, normalize_status_name, normalize_team_name,
    correct_over_under_line, normalize_market_outcome, format_odds
)
from common.utils.time import utc_to_cst
from common.exceptions import NormalizationError
from common.constants.urls import FANDUEL_URLS, FANDUEL_AUTH_TOKEN
from common.utils.client import PlaywrightSessionManager

class FanDuelClient(OddsClient):

    def __init__(self, league):
        super().__init__('fanduel', league)
        self.session = PlaywrightSessionManager.get_instance()


    def parse_schedule(self):
        url = FANDUEL_URLS[self.league]

        headers = {
            'origin': 'https://sportsbook.fanduel.com',
            'referer': 'https://sportsbook.fanduel.com',
        }
        params = {
            '_ak': FANDUEL_AUTH_TOKEN,
            'timezone': 'America%2FChicago'
        }
        data = self.fetch_data(url, headers=headers, params=params, method='playwright_request', context=self.session.context)

        event_count = len(data.get('attachments', {}).get('events', {}).values())
        self.logger.info(f'fetched {event_count} events ({self.league})')

        if not event_count:
            return

        events = data.get('attachments', {}).get('events', {}).values()
        for event in events:
            try:
                event_id = event['eventId']

                clean_name = re.sub(r'\s*\([^)]*\)', '', event['name']) # Remove primary player name inside parenthesis 
                teams = clean_name.split('@')
                away = normalize_team_name(teams[0], self.league)
                home = normalize_team_name(teams[1], self.league)

                start_time = utc_to_cst(event['openDate'])
                start_date = start_time.split('T')[0]

                event_key = create_event_key(self.league, start_date, away, home)
                self.match_espn_key(event_key, event_id)

            except NormalizationError as e:
                self.logger.debug(e)
            except Exception as e:
                self.logger.exception(f'an error occured while scraping events ({self.league}): {e}')

    
    def parse_primary_odds(self, status):
        url = FANDUEL_URLS[self.league]

        headers = {
            'origin': 'https://sportsbook.fanduel.com',
            'referer': 'https://sportsbook.fanduel.com',
        }
        params = {
            '_ak': FANDUEL_AUTH_TOKEN,
            'timezone': 'America%2FChicago'
        }
        data = self.fetch_data(url, headers=headers, params=params, method='playwright_request', context=self.session.context)

        market_count = len(data.get('attachments', {}).get('markets', {}).values())
        self.logger.info(f'fetched {market_count} markets ({self.league})')

        if not market_count:
            return

        status_keys = self.redis.smembers(f'espn:events:{self.league}:{status}')

        odds = []
        markets = data.get('attachments', {}).get('markets', {}).values()
        for market in markets:
            try:
                event_id = market['eventId']
                event_key = self.redis.get(f'{self.name}:keys:{event_id}')

                if not event_key or event_key not in status_keys:
                    continue

                market_name = market['marketName']

                selections = market['runners']
                for selection in selections:
                    outcome_name = selection['runnerName']
                    line = selection['handicap'] if selection['handicap'] else None
                    value = selection['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds']
                    status = selection['runnerStatus']

                    odds_data = self.parse_selection(event_key, market_name, outcome_name, line=line, value=value, status=status)
                    self.logger.info(f'name={market_name} | outcome={outcome_name} | line={line} | team=None | player=None -> {format_odds(odds_data)}')
                    if self.compare_and_update_odds_cache(odds_data):
                        odds.append(odds_data)

            except NormalizationError as e:
                self.logger.debug(e)
            except Exception as e:
                self.logger.exception(f'an error occured while scraping primary markets ({self.league}): {e}')
        
        self.upsert_data(odds)

    
    def parse_props(self, status):
        url = FANDUEL_URLS['event']

        status_keys = self.redis.smembers(f'espn:events:{self.league}:{status}')

        odds = []
        for event_key in status_keys:
            event_id = self.redis.get(f'{self.name}:ids:{event_key}')
            if not event_id:
                self.logger.warning(f'unknown event id for {event_key} ({self.league})')
                continue

            headers = {
                'origin': 'https://sportsbook.fanduel.com',
                'referer': 'https://sportsbook.fanduel.com',
            }
            params = {
                '_ak': FANDUEL_AUTH_TOKEN,
                'eventId': event_id,
                'tab': 'same-game-parlay-' if status == 'upcoming' else 'live-sgp'
            }
            data = self.fetch_data(url, headers=headers, params=params, method='playwright_request', context=self.session.context)

            market_count = len(data.get('attachments', {}).get('markets', {}))
            self.logger.info(f'fetched {market_count} markets for {event_key} ({self.league})')

            if not market_count:
                continue
            
            markets = data.get('attachments', {}).get('markets', {}).values()
            for market in markets:
                try:
                    market_name = market['marketName']

                    selections = market['runners']
                    for selection in selections:
                        outcome_name = selection['runnerName']
                        line = selection['handicap'] if selection['handicap'] else None
                        value = selection['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds']
                        status = selection['runnerStatus']

                        odds_data =  self.parse_selection(event_key, market_name, outcome_name, line=line, value=value, status=status)
                        self.logger.info(f'name={market_name} | outcome={outcome_name} | line={line} | team=None | player=None -> {format_odds(odds_data)}')
                        if self.compare_and_update_odds_cache(odds_data):
                            odds.append(odds_data)

                except NormalizationError as e:
                    self.logger.debug(e)
                except Exception as e:
                    self.logger.exception(f'an error occured while scraping prop markets ({self.league}): {e}')
        
        self.upsert_data(odds)
        

    def export_markets(self, event_keys=[]):
        url = FANDUEL_URLS['event']

        markets = { 'sportsbook': self.name, 'events': [] }
        for event_key in event_keys:
            event_markets = { 'event_key':  event_key, 'markets': [] }
            event_id = self.redis.get(f'{self.name}:ids:{event_key}')
            if not event_id:
                continue

            status = json.loads(self.redis.get(f'espn:events:{event_key}'))['status']

            headers = {
                'origin': 'https://sportsbook.fanduel.com',
                'referer': 'https://sportsbook.fanduel.com',
            }
            params = {
                '_ak': FANDUEL_AUTH_TOKEN,
                'eventId': event_id,
                'tab': 'same-game-parlay-' if status == 'upcoming' else 'live-sgp'
            }
            data = self.fetch_data(url, headers=headers, params=params, method='playwright_request', context=self.session.context)

            for market in data.get('attachments', {}).get('markets', {}).values():
                market_name = market['marketName']

                # Only store first outcome
                selections = market['runners']
                outcome = selections[0]['runnerName'] 
                line = selections[0].get('handicap', None)
                # FanDuel does not include these in seperate fields
                team = None
                player = None

                event_markets['markets'].append({
					'name': market_name,
					'outcome': outcome,
					'line': line,
					'team': team,
					'player': player,
                    'expected_outcome': {},
                    'expected_exception': False,
                })

            markets['events'].append(event_markets)
        
        return markets
