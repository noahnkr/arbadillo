import json
import re
from .base import SportsbookClient
from common.constants import FANDUEL_URLS
from common.utils import (
    normalize_team_name, normalize_market_name, create_event_key, 
	current_timestamp, generate_odds_hash, create_market_key, utc_to_cst, 
	format_odds, clean_str
)
from common.playwright_manager import PlaywrightSessionManager
from common.logging import configure_logging

logger = configure_logging(__name__)

class FanDuelClient(SportsbookClient):
    name = 'fanduel'

    def __init__(self, league):
        super().__init__(league)
        self.session = PlaywrightSessionManager.get_instance()


    def parse_schedule(self):
        url = FANDUEL_URLS[self.league]
        if url:
            logger.info(f'({self.name}) starting schedule request | league={self.league}, url={url}')
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
            except Exception as e:
                logger.exception(f'({self.name}) {e} occured while yielding schedule request | league={self.league}, url={url}')

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
                    if self.redis.hexists('espn:events', event_key):
                        self.redis.hset(f'{self.name}:events', event_id, event_key)
                        logger.info(f'({self.name}) successfully matched event key to ESPN schedule | league={self.league}, event_key={event_key}')
                    else:
                        logger.warning(f'({self.name}) unable to match event key to ESPN schedule | league={self.league}, event_key={event_key}')

                except Exception as e:
                    logger.exception(f'({self.name}) {e} occured while scraping event in schedule | league={self.league}')

        else:
            logger.warning(f'({self.name}) schedule url not found | league={self.league}')

    
    def parse_odds(self):
        url = FANDUEL_URLS[self.league]
        if url:
            logger.info(f'({self.name}) starting schedule request | league={self.league}, url={url}')
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
            except Exception as e:
                logger.exception(f'({self.name}) {e} occured while yielding odds request | league={self.league}, url={url}')

            for market in data['attachments']['markets'].values():
                try:
                    event_id = market['eventId']
                    if not self.redis.hexists(f'{self.name}:events', event_id):
                        continue

                    event_key = self.redis.hget(f'{self.name}:events', event_id)
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
                        logger.warning(f'({self.name}) market not supported | league={self.league}, market={market}')
                        continue

                    for i in range(len(markets)):
                        odds = {
                            'event_key': event_key,
                            'sportsbook': self.name,
                            'market': markets[i],
                            'outcome': outcomes[i],
                            'line': lines[i],
                            'value': values[i],
                            'player': None,
                            'prop': None,
                            'collected_at': current_timestamp()
                        }

                        market_key = create_market_key(markets[i], lines[i])
                        self.redis.sadd(f'{self.name}:markets:{event_key}', market_key)

                        odds_hash = generate_odds_hash(odds)
                        prev_hash = self.redis.hget(f'{self.name}:hashes:{event_key}:{market_key}', outcomes[i])
                        if prev_hash != odds_hash:
                            # Odds data have changed, cache odds and update DB
                            self.redis.hset(f'{self.name}:odds:{event_key}:{market_key}', outcomes[i], json.dumps(odds))
                            self.redis.hset(f'{self.name}:hashes:{event_key}:{market_key}', outcomes[i], odds_hash)
                            logger.info(f'({self.name}) cached {format_odds(odds)} | league={self.league}, event_key={event_key}')

                except Exception as e:
                    logger.exception(f'({self.name}) {e} occured while scraping odds | league={self.league}')

        else:
            logger.warning(f'({self.name}) schedule url not found | league={self.league}')