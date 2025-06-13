import json
from .base import SportsbookClient
from core.tasks import upsert_odds
from common.constants import DRAFTKINGS_URLS
from common.utils import (
    normalize_team_name, normalize_market_name, create_event_key, 
	generate_data_hash, create_market_key, utc_to_cst, format_odds,
)
from common.exceptions import NormalizationError

class DraftKingsClient(SportsbookClient):
	name = 'draftkings'

	def __init__(self, league):
		super().__init__(league)


	def parse_schedule(self):
		url = DRAFTKINGS_URLS[self.league]
		if url:
			self.logger.info(f'({self.name}) starting schedule request | league={self.league}, url={url}')
			try:
				data = self.fetch_data(url)
			except Exception as e:
				self.logger.critical(f'({self.name}) {e} occured while yielding schedule request | league={self.league}, url={url}')

			for event in data['events']:
				try:
					event_id = event['id']

					teams = event['name'].split('@')
					away = normalize_team_name(teams[0], self.league)
					home = normalize_team_name(teams[1], self.league)

					start_time = utc_to_cst(event['startEventDate'])
					start_date = start_time.split('T')[0]

					# Match event to ESPN schedule
					event_key = create_event_key(self.league, start_date, away, home)
					if self.redis.hexists('espn:events', event_key):
						self.redis.hset(f'{self.name}:events', event_id, event_key)
						self.logger.info(f'({self.name}) successfully matched event key to ESPN schedule | league={self.league}, event_key={event_key}')
					else:
						self.logger.warning(f'({self.name}) unable to match event key to ESPN schedule | league={self.league}, event_key={event_key}')

				except NormalizationError as e:
					self.logger.warning(f'({self.name}) {e}')
				except Exception as e:
					self.logger.exception(f'({self.name}) {e} occured while scraping event in schedule | league={self.league}')
					continue
		else:
			self.logger.warning(f'({self.name}) schedule url not found | league={self.league}')

			
		
	def parse_odds(self):
		url = DRAFTKINGS_URLS[self.league]
		if url:
			self.logger.info(f'({self.name}) starting odds request | league={self.league}, url={url}')
			try:
				data = self.fetch_data(url)
			except Exception as e:
				self.logger.critical(f'({self.name}) {e} occured while yielding odds request | league={self.league}, url={url}')
			
			# Each market (moneyline, spread, total, ...) has a unique market_id and event_id for its respective event
			for market in data['markets']:
				try:
					market_id = market['id']
					event_id = market['eventId']
					market = normalize_market_name(market['name'])

					self.redis.hset(
						f'{self.name}:markets',
						market_id, 
						json.dumps({
							'event_id': event_id,
							'market':  market,
					}))
				except Exception as e:
					self.logger.exception(f'({self.name}) {e} occured while scraping markets | league={self.league}')

			# Match each outcome selection to its respective market and event
			for selection in data['selections']:
				try:
					market_id = selection['marketId']
					selection_data = json.loads(self.redis.hget(f'{self.name}:markets', market_id))

					event_id = selection_data['event_id']
					if not self.redis.hexists(f'{self.name}:events', event_id):
						continue

					event_key = self.redis.hget(f'{self.name}:events', event_id)

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
						self.logger.warning(f'({self.name}) market not supported | league={self.league}, market={market}')
						continue

					market_key = create_market_key(market, line)
					self.redis.sadd(f'{self.name}:markets:{event_key}', market_key)

					value = selection['trueOdds']
					odds_data = {
						'event_key': event_key,
						'sportsbook': self.name,
						'market': market,
						'outcome': outcome,
						'line': line,
						'value': value,
						'player': None,
						'prop': None,
					}

					odds_hash = generate_data_hash(odds_data)
					prev_hash = self.redis.hget(f'{self.name}:hashes:{event_key}:{market_key}', outcome)
					if prev_hash != odds_hash:
						# Odds data have changed, cache odds and update DB
						upsert_odds.delay(odds_data)
						self.redis.hset(f'{self.name}:odds:{event_key}:{market_key}', outcome, json.dumps(odds_data))
						self.redis.hset(f'{self.name}:hashes:{event_key}:{market_key}', outcome, odds_hash)
						self.logger.info(f'({self.name}) stored {format_odds(odds_data)} | league={self.league}, event_key={event_key}')

				except NormalizationError as e:
					self.logger.warning(f'({self.name}) {e}')
				except Exception as e:
					self.logger.exception(f'({self.name}) {e} occured while scraping odds | league={self.league}')
		else:
			self.logger.warning(f'({self.name}) odds url not found | league={self.league}')

