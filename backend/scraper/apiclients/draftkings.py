import json
from .base import SportsbookClient
from common.constants import DRAFTKINGS_URLS
from common.utils import (
    normalize_team_name, normalize_market_name, create_event_key, 
	current_timestamp, generate_odds_hash, create_market_key, utc_to_cst, 
)
from common.logging import configure_logging

logger = configure_logging(__name__)

class DraftKingsClient(SportsbookClient):
	name = 'draftkings'

	def __init__(self, league=None):
		super().__init__(league)


	def parse_schedule(self):
		url = DRAFTKINGS_URLS[self.league]
		if url:
			logger.info(f'({self.name}) starting schedule request | league={self.league}, url={url}')
			try:
				data = self.fetch_data(url)
			except Exception as e:
				logger.critical(f'({self.name}) {e.with_traceback()} occured while yielding schedule request | league={self.league}, url={url}')

			for event in data['events']:
				try:
					event_id = event['id']

					name = event['name']
					participants = name.split('@')
					away = normalize_team_name(participants[0], self.league)
					home = normalize_team_name(participants[1], self.league)

					start_time = utc_to_cst(event['startEventDate'])
					start_date = start_time.split('T')[0]

					event_key = create_event_key(self.league, start_date, away, home)

					if self.redis.exists(f'espn:events:{event_key}') > 0 and self.redis.sismember('espn:events:active', event_key):
						# Match event to ESPN schedule
						self.redis.sadd(f'{self.name}:events', event_key)
						self.redis.set(f'{self.name}:events:{event_id}', event_key, ex=60 * 60 * 24)
						logger.info(f'({self.name}) successfully matched event key to ESPN schedule | event_key={event_key}')
					else:
						logger.warning(f'({self.name}) unable to match event key to ESPN schedule | event_key={event_key}')
				except Exception as e:
					logger.critical(f'({self.name}) {e.with_traceback()} occured while scraping event in schedule | league={self.league}')
					continue

			
		
	def parse_odds(self):
		url = DRAFTKINGS_URLS[self.league]
		if url:
			logger.info(f'({self.name}) starting odds request | league={self.league}, url={url}')
			try:
				data = self.fetch_data(url)
			except Exception as e:
				logger.critical(f'({self.name}) {e.with_traceback()} occured while yielding odds request | league={self.league}, url={url}')
			
			for market in data['markets']:
				try:
					market_id = market['id']
					event_id = market['eventId']
					market = normalize_market_name(market['name'])

					self.redis.set(
						f'{self.name}:markets:{market_id}', 
						json.dumps({
							'event_id': event_id,
							'market':  market,
					}))
				except Exception as e:
					logger.critical(f'({self.name}) {e.with_traceback()} occured while scraping markets | league={self.league}')

			for selection in data['selections']:
				try:
					market_id = selection['marketId']
					selection_data = json.loads(
						self.redis.get(f'{self.name}:markets:{market_id}')
					)

					event_id = selection_data['event_id']
					event_key = self.redis.get(f'{self.name}:events:{event_id}')
					if not event_key or not self.redis.sismember(f'{self.name}:events', event_key):
						continue

					value = selection['trueOdds']
					market = selection_data['market']
					if market == 'moneyline':
						outcome = normalize_team_name(selection['label'], self.league)
						line = None
					elif market == 'spread':
						outcome = normalize_team_name(selection['label'], self.league)
						line = selection['points']
					elif market == 'total':
						outcome = selection['label'].lower()
						line = selection['points']
					else:
						logger.warning(f'({self.name}) market not supported | league={self.league}, market={market}')
						continue

					market_key = create_market_key(market, line)
					self.redis.sadd(f'{self.name}:markets:{event_key}', market_key)

					odds = {
						'event_key': event_key,
						'sportsbook': self.name,
						'market': market,
						'outcome': outcome,
						'line': line,
						'value': value,
						'player': None,
						'prop': None,
						'collected_at': current_timestamp()
					}

					odds_hash = generate_odds_hash(odds)
					prev_hash = self.redis.hget(f'{self.name}:hashes:{event_key}:{market_key}', outcome)
					if prev_hash != odds_hash:
						# Odds data have changed, cache odds and update DB
						self.redis.hset(f'{self.name}:odds:{event_key}:{market_key}', outcome, json.dumps(odds))
						self.redis.hset(f'{self.name}:hashes:{event_key}:{market_key}', outcome, odds_hash)
						logger.info(f'({self.name}) cached {market} odds | league={self.league}, event_key={event_key}')

				except Exception as e:
					logger.critical(f'({self.name}) {e.with_traceback()} occured while scraping odds | league={self.league}')
		else:
			logger.warning(f'({self.name}) url not found | league={self.league}')

