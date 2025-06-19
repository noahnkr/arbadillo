import json
import re
from .base import SportsbookClient
from scraper.tasks import batch_upsert_odds
from common.constants.urls import FANDUEL_URLS
from common.constants.sportsbook import (
    EVENT_EXPIRATION_TIME, ODDS_EXPIRATION_TIME, PRIMARY_MARKETS,
)
from common.utils import (
    normalize_team_name, normalize_market_name, create_event_key, generate_data_hash, 
    create_market_key, utc_to_cst, format_odds, normalize_status_name, extract_float, extract_text,
)
from common.exceptions import NormalizationError
from common.playwright_manager import PlaywrightSessionManager

class FanDuelClient(SportsbookClient):

    def __init__(self, league):
        super().__init__('fanduel', league)
        self.session = PlaywrightSessionManager.get_instance()


    def parse_schedule(self):
        url = FANDUEL_URLS[self.league]
        if not url:
            self.logger.warning(f'schedule url not found ({self.league})')
            return

        self.logger.info(f'starting schedule request ({self.league})')
        try:
            headers = {
                'origin': 'https://sportsbook.fanduel.com',
                'referer': 'https://sportsbook.fanduel.com',
            }
            params = {
                '_ak': 'FhMFpcPWXMeyZxOx',
                'timezone': 'America%2FChicago'
            }
            data = self.fetch_data(url, headers=headers, params=params, session=self.session)
            event_count = len(data.get('attachments', {}).get('events', {}).values())
            self.logger.info(f'fetched {event_count} events ({self.league})')
        except Exception as e:
            self.logger.exception(f'{e} occured while yielding schedule request to {url} ({self.league})')

        events = data.get('attachments', {}).get('events', {}).values()
        for event in events:
            try:
                event_id = event['eventId']

                # Remove starting pitchers from name for MLB events
                clean_name = re.sub(r'\s*\([^)]*\)', '', event['name'])
                teams = clean_name.split('@')
                if len(teams) != 2:
                    continue

                away = normalize_team_name(teams[0], self.league)
                home = normalize_team_name(teams[1], self.league)

                start_time = utc_to_cst(event['openDate'])
                start_date = start_time.split('T')[0]

                # Match event to ESPN schedule
                event_key = create_event_key(self.league, start_date, away, home)
                if self.redis.exists(f'espn:events:{event_key}'):
                    self.redis.set(f'{self.name}:keys:{event_id}', event_key, ex=EVENT_EXPIRATION_TIME)
                    self.redis.set(f'{self.name}:ids:{event_key}', event_id, ex=EVENT_EXPIRATION_TIME)
                    self.logger.info(f'matched {event_key}')
                else:
                    self.logger.warning(f'unable to match {event_key}')

            except NormalizationError as e:
                self.logger.warning(f'{e} ({self.league})')
            except Exception as e:
                self.logger.exception(f'{e} occured while scraping events ({self.league})')

    
    def parse_primary_odds(self, status):
        url = FANDUEL_URLS[self.league]
        if not url:
            self.logger.warning(f'primary odds url not found ({self.league})')
            return

        self.logger.info(f'starting primary odds request ({self.league})')
        try:
            headers = {
                'origin': 'https://sportsbook.fanduel.com',
                'referer': 'https://sportsbook.fanduel.com',
            }
            params = {
                '_ak': 'FhMFpcPWXMeyZxOx',
                'timezone': 'America%2FChicago'
            }
            data = self.fetch_data(url, headers=headers, params=params, session=self.session)
            market_count = len(data.get('attachments', {}).get('markets', {}).values())
            self.logger.info(f'fetched {market_count} markets ({self.league})')
        except Exception as e:
            self.logger.exception(f'{e} occured while yielding primary odds request to {url} ({self.league})')

        status_keys = self.redis.smembers(f'espn:events:{status}')

        primary = []
        markets = data.get('attachments', {}).get('markets', {}).values()
        for market in markets:
            try:
                event_id = market['eventId']
                event_key = self.redis.get(f'{self.name}:keys:{event_id}')
                if not event_key or event_key not in status_keys:
                    continue

                market_name, market_type, scope, line, outcome = normalize_market_name(market['marketName'], self.league)
                if market_name not in PRIMARY_MARKETS:
                    continue

                runner_odds = self.parse_runners(market, event_key, market_name, market_type, scope, line, outcome)

                for odds_data in runner_odds:
                    odds_hash = generate_data_hash(odds_data)
                    redis_key = f'{self.name}:odds:{event_key}:{odds_data["market_key"]}:{odds_data["outcome"]}'
                    redis_hash_key = f'{self.name}:hashes:{event_key}:{odds_data["market_key"]}:{odds_data["outcome"]}'
                    prev_hash = self.redis.get(redis_hash_key)

                    if prev_hash != odds_hash:
                        primary.append(odds_data)
                        self.redis.set(redis_key, json.dumps(odds_data), ex=ODDS_EXPIRATION_TIME)
                        self.redis.set(redis_hash_key, odds_hash, ex=ODDS_EXPIRATION_TIME)
                        self.logger.info(f'scraped {format_odds(odds_data, odds_data["market"])} for {event_key}')

            except NormalizationError as e:
                self.logger.warning(f'{e} ({self.league})')
            except Exception as e:
                self.logger.exception(f'{e} occured while scraping primary odds ({self.league})')

        if not primary:
            self.logger.info(f'no new primary odds to upsert ({self.league})')
        else:
            self.logger.info(f'upserting {len(primary)} primary odds ({self.league})')
            batch_upsert_odds.delay(primary)

    
    def parse_props(self, status):
        url = FANDUEL_URLS['event']
        self.logger.info(f'starting props request ({self.league})')
        keys = self.redis.smembers(f'espn:events:{status}')

        props = []
        for event_key in keys:
            event_id = self.redis.get(f'{self.name}:ids:{event_key}')
            if not event_id:
                self.logger.warning(f'unknown event id for {event_key} ({self.league})')
                continue

            try:
                headers = {
                    'origin': 'https://sportsbook.fanduel.com',
                    'referer': 'https://sportsbook.fanduel.com',
                }
                params = {
                    '_ak': 'FhMFpcPWXMeyZxOx',
                    'eventId': event_id,
                    'tab': 'same-game-parlay' if status == 'upcoming' else 'live-sgp'
                }
                prop_data = self.fetch_data(url, headers=headers, params=params, session=self.session)
                market_count = len(prop_data.get('attachments', {}).get('markets', {}))
                self.logger.info(f'fetched {market_count} markets for {event_key} ({self.league})')
            except Exception as e:
                self.logger.warning(f'{e} occured while yielding prop request to {url} for {event_key} ({self.league})')
                continue
            
            try:
                props.extend(self.parse_event_props(event_key, prop_data))
            except Exception as e:
                self.logger.exception(f'{e} occured while scraping props for {event_key} ({self.league})')
                
        if not props:
            self.logger.info(f'no new props to upsert ({self.league})')
        else:
            self.logger.info(f'upserting {len(props)} props ({self.league})')
            batch_upsert_odds.delay(props)


    def parse_event_props(self, event_key, prop_data) -> list[dict]:
        event_props = []
        markets = prop_data.get('attachments', {}).get('markets', {}).values()
        for prop in markets:
            try:
                market_name, market_type, scope, line, outcome = normalize_market_name(prop['marketName'], self.league)
                if market_name in PRIMARY_MARKETS:
                    continue
                event_props.extend(self.parse_runners(prop['runners'], event_key, market_name, market_type, scope, line, outcome))
            except NormalizationError as e:
                self.logger.warning(f'{e} ({self.league})')
            except Exception as e:
                self.logger.exception(f'{e} occured while scraping props for {event_key} ({self.league})')
        
        return event_props


    def parse_runners(self, runners, event_key, market_name, market_type, scope, line, outcome) -> list[dict]:
        """Parses runners and returns a list of odd selection dicts."""
        selections = []

        if market_type == 'moneyline':
            for runner in runners:
                selections.append({
                    'event_key': event_key,
                    'market_key': market_name,
                    'sportsbook': self.name,
                    'market': market_name,
                    'outcome': normalize_team_name(runner['runnerName'], self.league),
                    'line': None,
                    'value': runner['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds'],
                    'team': None,
                    'player': None,
                    'status': normalize_status_name(runner['runnerStatus'], event=False)
                })

        elif market_type in {'spread', 'total'}:
            for runner in runners:
                line = runner['handicap']
                if line == 0:
                    line = extract_float(runner['runnerName'])

                outcome = extract_text(runner['runnerName'])
                if not outcome:
                    self.logger.warning(f'unable to extract outcome from runner name `{runner["runnerName"]}`')
                    continue

                market_key = create_market_key(market_name, line)
                
                selections.append({
                    'event_key': event_key,
                    'market_key': market_key,
                    'sportsbook': self.name,
                    'market': market_name,
                    'outcome': outcome,
                    'line': line,
                    'value': runner['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds'],
                    'team': None,
                    'player': None,
                    'status': normalize_status_name(runner['runnerStatus'], event=False)
                })
        elif market_type in {'over_under', 'yes_no'}:
            for runner in runners:
                if not line and market_type == 'over_under':
                    line = runner['handicap']
                if not outcome and market_type == 'over_under':
                    outcome = runner['result']['type'].lower()
                if not outcome and market_type  == 'yes_no':
                    outcome = runner['runnerName'].lower()

                if scope in {'team', 'player'}:
                    team = None # TODO: handle team names
                    player = runner['runnerName']
                    market_key = create_market_key(market_name, line, player=player)
                else:
                    team = None
                    player = scope
                    market_key = create_market_key(market_name, line, player=player)

                selections.append({
                    'event_key': event_key,
                    'market_key': market_key,
                    'sportsbook': self.name,
                    'market': market_name,
                    'outcome': outcome,
                    'line': line,
                    'value': runner['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds'],
                    'team': team,
                    'player': player,
                    'status': normalize_status_name(runner['runnerStatus'], event=False)
                })

        return selections