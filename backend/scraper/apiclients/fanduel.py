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
    create_market_key, utc_to_cst, format_odds, normalize_status_name
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
            self.logger.info(f'fetched {len(data["attachments"]["events"].values())} events ({self.league})')
        except Exception as e:
            self.logger.exception(f'{e} occured while yielding schedule request to {url} ({self.league})')

        for event in data['attachments']['events'].values():
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
            self.logger.warning(f'odds url not found ({self.league})')
            return

        self.logger.info(f'starting odds request ({self.league})')
        keys = self.redis.smembers(f'espn:events:{status}')
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
            self.logger.info(f'fetched {len(data["attachments"]["markets"].values())} markets ({self.league})')
        except Exception as e:
            self.logger.exception(f'{e} occured while yielding odds request to {url} ({self.league})')

        primary = []
        for market in data['attachments']['markets'].values():
            try:
                event_id = market['eventId']
                event_key = self.redis.get(f'{self.name}:keys:{event_id}')
                if not event_key or event_key not in keys:
                    continue

                market_name = normalize_market_name(market['marketName'], self.league)
                if market_name not in PRIMARY_MARKETS:
                    continue

                odds_entries = self.parse_runners(market, market_name, self.league)

                for entry in odds_entries:
                    market_key = create_market_key(entry['market'], entry['line'])
                    odds_data = {
                        'event_key': event_key,
                        'market_key': market_key,
                        'sportsbook': self.name,
                        'market': entry['market'],
                        'outcome': entry['outcome'],
                        'line': entry['line'],
                        'value': entry['value'],
                        'team': None,
                        'player': None,
                        'status': entry['statuts'],
                    }

                    odds_hash = generate_data_hash(odds_data)
                    redis_key = f'{self.name}:odds:{event_key}:{market_key}:{entry["outcome"]}'
                    redis_hash_key = f'{self.name}:hashes:{event_key}:{market_key}:{entry["outcome"]}'
                    prev_hash = self.redis.get(redis_hash_key)

                    if prev_hash != odds_hash:
                        primary.append(odds_data)
                        self.redis.set(redis_key, json.dumps(odds_data), ex=ODDS_EXPIRATION_TIME)
                        self.redis.set(redis_hash_key, odds_hash, ex=ODDS_EXPIRATION_TIME)
                        self.logger.info(f'scraped {format_odds(odds_data, entry["market"])} for {event_key}')

            except NormalizationError as e:
                self.logger.warning(f'{e} ({self.league})')
            except Exception as e:
                self.logger.exception(f'{e} occured while scraping odds ({self.league})')

        if not primary:
            self.logger.info(f'no new odds to upsert ({self.league})')
        else:
            self.logger.info(f'upserting {len(primary)} odds ({self.league})')
            batch_upsert_odds.delay(primary)


    def parse_runners(self, market, market_name, league):
        """Parses runners and returns a list of odds_data entries."""
        runners = market['runners']
        odds_entries = []

        if market_name in {'moneyline', 'spread'}:
            for runner in runners:
                odds_entries.append({
                    'market': market_name,
                    'outcome': normalize_team_name(runner['runnerName'], league),
                    'line': None if market_name == 'moneyline' else runner['handicap'],
                    'value': runner['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds'],
                    'status': normalize_status_name(runner['runnerStatus'], event=False)
                })
        elif market_name == 'total':
            for i, runner in enumerate(runners):
                odds_entries.append({
                    'market': 'total',
                    'outcome': 'over' if i == 0 else 'under',
                    'line': runner['handicap'],
                    'value': runner['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds'],
                    'status': normalize_status_name(runner['runnerStatus'], event=False)
                })
        return odds_entries
    

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
                    'tab': 'popular',
                }
                prop_data = self.fetch_data(url, headers=headers, params=params, session=self.session)
                self.logger.info(f'fetched {len(prop_data["attachments"]["markets"])} markets for {event_key} ({self.league})')
            except Exception as e:
                self.logger.warning(f'{e} occured while yielding prop request to {url} for {event_key} ({self.league})')
                continue
            
            try:
                event_props = self.parse_event_props(event_key, prop_data)
                props.extend(event_props)
            except Exception as e:
                self.logger.exception(f'{e} occured while scraping props for {event_key} ({self.league})')
                
        if not props:
            self.logger.info(f'no new props to upsert ({self.league})')
        else:
            self.logger.info(f'upserting {len(props)} props ({self.league})')
            batch_upsert_odds.delay(props)


    def parse_event_props(self, event_key, prop_data) -> list:
        event_props = []
        for prop in prop_data['attachments']['markets'].values():
            try:
                market, market_type, line = normalize_market_name(prop['marketName'], self.league)
                # No need to collect primary markets
                if market in PRIMARY_MARKETS:
                    continue

                scope = 'team' if 'team' in market else 'player'

                for selection in prop['runners']:
                    pass


            except NormalizationError as e:
                self.logger.warning(f'{e} ({self.league})')
            except Exception as e:
                self.logger.exception(f'{e} occured while scraping props for {event_key} ({self.league})')