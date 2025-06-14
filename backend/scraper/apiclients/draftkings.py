import json
from .base import SportsbookClient
from scraper.tasks import batch_upsert_odds
from common.constants import DRAFTKINGS_URLS, EVENT_EXPIRATION_TIME, ODDS_EXPIRATION_TIME
from common.utils import (
	normalize_team_name, normalize_market_name, create_event_key, 
	generate_data_hash, create_market_key, utc_to_cst, decimal_to_american,
)
from common.exceptions import NormalizationError

class DraftKingsClient(SportsbookClient):

	def __init__(self, league):
		super().__init__('draftkings', league)


	def parse_schedule(self):
		url = DRAFTKINGS_URLS[self.league]
		if not url:
			self.logger.warning(f'schedule url not found ({self.league})')
			return

		self.logger.info(f'starting schedule request ({self.league})')
		try:
			data = self.fetch_data(url)
			self.logger.info(f'fetched {len(data["events"])} events ({self.league})')
		except Exception as e:
			self.logger.critical(f'{e} occured while yielding schedule request to {url} ({self.league})')

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
				if self.redis.exists(f'espn:events:{event_key}'):
					self.redis.set(f'{self.name}:events:{event_id}', event_key, ex=EVENT_EXPIRATION_TIME)
					self.logger.info(f'matched {event_key}')
				else:
					self.logger.warning(f'unable to match {event_key}')

			except NormalizationError as e:
				self.logger.warning(f'{e} ({self.league})')
			except Exception as e:
				self.logger.exception(f'{e} occured while scraping events ({self.league})')
				continue

		
	def parse_odds(self):
		url = DRAFTKINGS_URLS[self.league]
		if not url:
			self.logger.warning(f'odds url not found ({self.league})')
			return

		self.logger.info(f'starting odds request ({self.league})')
		try:
			data = self.fetch_data(url)
			self.logger.info(f'fetched {len(data["markets"])} markets and {len(data["selections"])} selections ({self.league})')
		except Exception as e:
			self.logger.critical(f'{e} occured while yielding odds request to {url} ({self.league})')
		
		# Each market (moneyline, spread, total, ...) has a unique market_id and event_id for its respective event
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
					}),
					ex=ODDS_EXPIRATION_TIME,
				)
			except Exception as e:
				self.logger.exception(f'{e} occured while scraping markets ({self.league})')

		# Match each outcome selection to its respective market and event
		odds = []
		for selection in data['selections']:
			try:
				market_id = selection['marketId']
				selection_data = json.loads(self.redis.get(f'{self.name}:markets:{market_id}'))

				event_id = selection_data['event_id']
				if not self.redis.exists(f'{self.name}:events:{event_id}'):
					continue

				event_key = self.redis.get(f'{self.name}:events:{event_id}')

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
					self.logger.warning(f'{market} market not supported ({self.league})')
					continue

				value = selection['trueOdds']
				market_key = create_market_key(market, line)

				odds_data = {
					'event_key': event_key,
					'market_key': market_key,
					'sportsbook': self.name,
					'market': market,
					'outcome': outcome,
					'line': line,
					'value': value,
					'player': None,
					'prop': None,
				}

				odds_hash = generate_data_hash(odds_data)
				prev_hash = self.redis.get(f'{self.name}:hashes:{event_key}:{market_key}:{outcome}')
				if prev_hash != odds_hash:
					# Odds data have changed, cache odds and update DB
					odds.append(odds_data)
					self.redis.set(f'{self.name}:odds:{event_key}:{market_key}:{outcome}', json.dumps(odds_data), ex=ODDS_EXPIRATION_TIME)
					self.redis.set(f'{self.name}:hashes:{event_key}:{market_key}:{outcome}', odds_hash, ex=ODDS_EXPIRATION_TIME)
					self.logger.info(f'scraped {market_key} [{decimal_to_american(value)}] for {event_key}')

			except NormalizationError as e:
				self.logger.warning(f'{e} ({self.league})')
			except Exception as e:
				self.logger.exception(f'{e} occured while scraping odds ({self.league})')

		if not odds:
			self.logger.info(f'no new odds to upsert ({self.league})')
		else:
			self.logger.info(f'upserting {len(odds)} odds ({self.league})')
			batch_upsert_odds.delay(odds)