import json
import re
from .base import SportsbookClient
from scraper.tasks import batch_upsert_odds
from common.constants import FANDUEL_URLS, EVENT_EXPIRATION_TIME, ODDS_EXPIRATION_TIME
from common.utils import (
    normalize_team_name, normalize_market_name, create_event_key, 
	generate_data_hash, create_market_key, utc_to_cst, decimal_to_american,
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
                    self.redis.set(f'{self.name}:events:{event_id}', event_key, ex=EVENT_EXPIRATION_TIME)
                    self.logger.info(f'matched {event_key}')
                else:
                    self.logger.warning(f'unable to match {event_key}')

            except NormalizationError as e:
                self.logger.warning(f'{e} ({self.league})')
            except Exception as e:
                self.logger.exception(f'{e} occured while scraping events ({self.league})')

    
    def parse_odds(self):
        url = FANDUEL_URLS[self.league]
        if not url:
            self.logger.warning(f'odds url not found ({self.league})')
            return

        self.logger.info(f'starting odds request ({self.league})')
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

        odds = []
        for market in data['attachments']['markets'].values():
            try:
                event_id = market['eventId']
                if not self.redis.exists(f'{self.name}:events:{event_id}'):
                    continue

                event_key = self.redis.get(f'{self.name}:events:{event_id}')
                market_name = normalize_market_name(market['marketName'])
                markets, outcomes, lines, values = [], [], [], []

                if market_name == 'moneyline':
                    markets.extend(['moneyline', 'moneyline'])
                    outcomes.extend([
                        normalize_team_name(market['runners'][0]['runnerName'], self.league),
                        normalize_team_name(market['runners'][1]['runnerName'], self.league)
                    ])
                    lines.extend([None, None])
                    values.extend([
                        market['runners'][0]['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds'],
                        market['runners'][1]['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds']
                    ])
                elif market_name == 'spread':
                    markets.extend(['spread', 'spread'])
                    outcomes.extend([
                        normalize_team_name(market['runners'][0]['runnerName'], self.league),
                        normalize_team_name(market['runners'][1]['runnerName'], self.league)
                    ])
                    lines.extend([
                        market['runners'][0]['handicap'],
                        market['runners'][1]['handicap']
                    ])
                    values.extend([
                        market['runners'][0]['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds'],
                        market['runners'][1]['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds']
                    ])
                elif market_name == 'total':
                    markets.extend(['total', 'total'])
                    outcomes.extend(['over', 'under'])
                    lines.extend([
                        market['runners'][0]['handicap'],
                        market['runners'][1]['handicap']
                    ])
                    values.extend([
                        market['runners'][0]['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds'],
                        market['runners'][1]['winRunnerOdds']['trueOdds']['decimalOdds']['decimalOdds']
                    ])
                else:
                    self.logger.warning(f'market not supported | league={self.league}, market={market}')
                    continue

                for i in range(len(markets)):
                    market_key = create_market_key(markets[i], lines[i])
                    odds_data = {
                        'event_key': event_key,
                        'market_key': market_key,
                        'sportsbook': self.name,
                        'market': markets[i],
                        'outcome': outcomes[i],
                        'line': lines[i],
                        'value': values[i],
                        'player': None,
                        'prop': None,
                    }

                    odds_hash = generate_data_hash(odds_data)
                    prev_hash = self.redis.get(f'{self.name}:hashes:{event_key}:{market_key}:{outcomes[i]}')
                    if prev_hash != odds_hash:
                        # Odds data have changed, cache odds and update DB
                        odds.append(odds_data)
                        self.redis.set(f'{self.name}:odds:{event_key}:{market_key}:{outcomes[i]}', json.dumps(odds_data), ex=ODDS_EXPIRATION_TIME)
                        self.redis.set(f'{self.name}:hashes:{event_key}:{market_key}:{outcomes[i]}', odds_hash, ex=ODDS_EXPIRATION_TIME)
                        self.logger.info(f'scraped {market_key} ({decimal_to_american(values[i])}) for {event_key}')

            except NormalizationError as e:
                self.logger.warning(f'{e} ({self.league})')
            except Exception as e:
                self.logger.exception(f'{e} occured while scraping odds ({self.league})')

        if not odds:
            self.logger.info(f'no new odds to upsert ({self.league})')
        else:
            self.logger.info(f'upserting {len(odds)} odds ({self.league})')
            batch_upsert_odds.delay(odds)