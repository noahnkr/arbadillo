import json
from .base import SportsbookClient
from scraper.tasks import batch_upsert_odds
from common.constants.urls import DRAFTKINGS_URLS
from common.constants.sportsbook import EVENT_EXPIRATION_TIME, ODDS_EXPIRATION_TIME, PRIMARY_MARKETS
from common.utils import (
	normalize_team_name, normalize_market_name, create_event_key, 
	generate_data_hash, create_market_key, utc_to_cst, format_odds, extract_float
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
			headers = {
                'origin': 'https://sportsbook.draftkings.com',
                'referer': 'https://sportsbook.draftkings.com',
            }
			data = self.fetch_data(url, headers=headers)
			event_count = len(data.get('events', {}))
			self.logger.info(f'fetched {event_count} events ({self.league})')
		except Exception as e:
			self.logger.exception(f'{e} occured while yielding schedule request to {url} ({self.league})')

		events = data.get('events', {})
		for event in events:
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
		url = DRAFTKINGS_URLS[self.league]
		if not url:
			self.logger.warning(f'primary odds url not found ({self.league})')
			return

		self.logger.info(f'starting odds request ({self.league})')
		try:
			headers = {
                'origin': 'https://sportsbook.draftkings.com',
                'referer': 'https://sportsbook.draftkings.com',
            }
			data = self.fetch_data(url, headers=headers)
			market_count = len(data.get('markets', {})) 
			self.logger.info(f'fetched {market_count} markets ({self.league})')
		except Exception as e:
			self.logger.exception(f'{e} occured while yielding primary odds request to {url} ({self.league})')
		
		# Each market (moneyline, spread, total, ...) has a unique market_id and event_id for its respective event
		markets = data.get('markets', {})
		for market in markets:
			try:
				market_id = market['id']
				event_id = market['eventId']
				raw_market = market['marketType']['name']
				market_name, market_type, _, _, _ = normalize_market_name(raw_market, self.league)

				self.redis.set(
					f'{self.name}:markets:{market_id}',
					json.dumps({
						'event_id': event_id,
						'market':  market_name,
						'type': market_type,
					}),
					ex=ODDS_EXPIRATION_TIME,
				)
			except NormalizationError as e:
				self.logger.warning()
			except Exception as e:
				self.logger.exception(f'{e} occured while scraping primary markets ({self.league})')

		status_keys = self.redis.smembers(f'espn:events:{status}')
		# Match each outcome selection to its respective market and event
		primary = []
		selections = data.get('selections', {})
		for selection in selections:
			try:
				market_id = selection['marketId']
				market_data = json.loads(self.redis.get(f'{self.name}:markets:{market_id}'))

				event_id = market_data['event_id']
				event_key = self.redis.get(f'{self.name}:keys:{event_id}')
				if not event_key or event_key not in status_keys:
					continue

				market_name = market_data['market']
				market_type = market_data['type']
				if market_name not in PRIMARY_MARKETS:
					continue

				primary_data = self.parse_selection(selection, event_key, market_name, market_type)

				primary_hash = generate_data_hash(primary_data)
				redis_key = f'{self.name}:odds:{event_key}:{primary_data["market_key"]}:{primary_data["outcome"]}'
				redis_hash_key = f'{self.name}:hashes:{event_key}:{primary_data["market_key"]}:{primary_data["outcome"]}'
				prev_hash = self.redis.get(redis_hash_key)

				if prev_hash != primary_hash:
					# Odds data have changed, cache odds and update DB
					primary.append(primary_data)
					self.redis.set(redis_key, json.dumps(primary_data), ex=ODDS_EXPIRATION_TIME)
					self.redis.set(redis_hash_key, primary_hash, ex=ODDS_EXPIRATION_TIME)
					self.logger.info(f'scraped {format_odds(primary_data)} for {event_key}')

			except NormalizationError as e:
				self.logger.warning(f'{e} ({self.league})')
			except Exception as e:
				self.logger.exception(f'{e} occured while scraping primary selections ({self.league})')

		if not primary:
			self.logger.info(f'no new odds to upsert ({self.league})')
		else:
			self.logger.info(f'upserting {len(primary)} odds ({self.league})')
			batch_upsert_odds.delay(primary)
	

	def parse_props(self, status):
		url = DRAFTKINGS_URLS['event']
		self.logger.info(f'starting props request ({self.league})')
		status_keys = self.redis.smembers(f'espn:events:{status}')

		for event_key in status_keys:
			event_id = self.redis.get(f'{self.name}:ids:{event_key}')
			if not event_id:
				self.logger.warning(f'unknown event id for {event_key} ({self.league})')
				continue

			try:
				headers = {
					'origin': 'https://sportsbook.draftkings.com',
					'referer': 'https://sportsbook.draftkings.com',
				}
				url += f'/{event_id}/categories'
				data = self.fetch_data(url, headers=headers)
				market_count = len(data.get('markets', {})) 
				self.logger.info(f'fetched {market_count} markets ({self.league})')
			except Exception as e:
				self.logger.warning(f'{e} occured while yielding prop request to {url} for {event_key} ({self.league})')
				continue
			
			markets = data.get('markets', {})
			for market in markets:
				try:
					market_id = market['id']
					raw_market = market['name']
					market_name, market_type, _, _, _ = normalize_market_name(raw_market, self.league)

					self.redis.set(
						f'{self.name}:markets:{market_id}',
						json.dumps({
							'event_id': event_id,
							'market':  market_name,
							'type': market_type,
						}),
						ex=ODDS_EXPIRATION_TIME,
					)
				except NormalizationError as e:
					self.logger.warning(f'{e} ({self.league})')
				except Exception as e:
					self.logger.exception(f'{e} occured while scraping prop markets ({self.league})')

			props = []
			selections = data.get('selections', {})
			for selection in selections:
				try:
					market_id = selection['marketId']
					market_data = json.loads(self.redis.get(f'{self.name}:markets:{market_id}'))

					market_name = market_data['market']
					market_type = market_data['type']
					if market_name in PRIMARY_MARKETS:
						continue

					prop_data = self.parse_selection(selection, event_key, market_name, market_type)

					primary_hash = generate_data_hash(prop_data)
					redis_key = f'{self.name}:odds:{event_key}:{prop_data["market_key"]}:{prop_data["outcome"]}'
					redis_hash_key = f'{self.name}:hashes:{event_key}:{prop_data["market_key"]}:{prop_data["outcome"]}'
					prev_hash = self.redis.get(redis_hash_key)

					if prev_hash != primary_hash:
						# Odds data have changed, cache odds and update DB
						props.append(prop_data)
						self.redis.set(redis_key, json.dumps(prop_data), ex=ODDS_EXPIRATION_TIME)
						self.redis.set(redis_hash_key, primary_hash, ex=ODDS_EXPIRATION_TIME)
						self.logger.info(f'scraped {format_odds(prop_data)} for {event_key}')

				except NormalizationError as e:
					self.logger.warning(f'{e} ({self.league})')
				except Exception as e:
					self.logger.exception(f'{e} occured while scraping primary selections ({self.league})')
	
	def parse_selection(self, selection, event_key, market_name, market_type):
		label = selection['label']

		line = None
		team = None
		player = None

		if market_type == 'moneyline':
			outcome = normalize_team_name(label, self.league)
		elif market_type in {'spread', 'total'}:
			outcome = normalize_team_name(label, self.league)
			line = selection['points']
		elif market_type in {'over_under', 'yes_no'}:
			if label.lower() in {'over', 'under'}:
				outcome = label.lower()
				line = selection['points']
			elif '+' in label.lower():
				outcome = 'over'
				line = extract_float(label)
				line -= 0.5
			elif label.lower() in {'yes', 'no'}:
				outcome = label.lower()
			else:
				raise NormalizationError(f'unknown selection line format for {market_type} `{market_name}`: {label}')

			participant = selection['participants'][0] 
			scope = participant['type'].lower()
			if scope == 'player':
				player = participant['name']
			elif scope == 'team':
				league = event_key.split(':')[0]
				team = normalize_team_name(participant['name'], league)
			else:
				raise NormalizationError(f'unknown selection scope for over_under `{market_name}`: {scope}')
		else:
			raise NormalizationError(f'unknown market_type `{market_type}`')

		value = round(selection['trueOdds'], 3)
		market_key = create_market_key(market_name, line, team, player)
		status = 'active' # TODO: determine market status

		return {
			'event_key': event_key,
			'market_key': market_key,
			'sportsbook': self.name,
			'market': market_name,
			'outcome': outcome,
			'line': line,
			'value': value,
			'team': team,
			'player': player,
			'status': status
		}