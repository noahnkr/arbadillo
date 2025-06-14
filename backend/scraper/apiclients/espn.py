import json
from datetime import datetime, timedelta
from dateutil import tz
from .base import SportsbookClient
from scraper.tasks import batch_upsert_events, batch_upsert_odds
from common.constants import ESPN_URLS, ESPNBET_URLS, EVENT_EXPIRATION_TIME, ODDS_EXPIRATION_TIME
from common.utils import (
	normalize_team_name, normalize_status_name, create_event_key, create_market_key, 
	utc_to_cst, generate_data_hash, extract_float, decimal_to_american,
)
from common.exceptions import NormalizationError

class ESPNClient(SportsbookClient):
	def __init__(self, league):
		super().__init__('espn', league)


	def parse_schedule(self):
		url = ESPN_URLS[self.league]
		if not url:
			self.logger.warning(f'schedule url not found ({self.league})')
			return

		self.logger.info(f'starting schedule request ({self.league})')
		try:
			central = tz.gettz('America/Chicago')
			today = datetime.now(tz=central).strftime('%Y%m%d')
			today_data = self.fetch_data(url, params={'dates': today})

			tomorrow = (datetime.now(tz=central) + timedelta(days=1)).strftime('%Y%m%d')
			tomorrow_data = self.fetch_data(url, params={'dates': tomorrow})

			event_data = today_data['events'] + tomorrow_data['events']
			self.logger.info(f'fetched {len(event_data)} events ({self.league})')
		except Exception as e:
			self.logger.exception(f'{e} occured while yielding schedule request to {url} ({self.league})')

		events = []
		for event in event_data:
			try:
				event_id = event['id']

				start_time = utc_to_cst(event['date'])
				start_date = start_time.split('T')[0]

				teams = event['shortName'].split('@')
				away = normalize_team_name(teams[0], self.league)
				home = normalize_team_name(teams[1], self.league)

				event_key = create_event_key(self.league, start_date, away, home)

				status = normalize_status_name(event['status']['type']['state'])
				if status in ['upcoming', 'active']:
					self.redis.sadd(f'{self.name}:events:{self.league}:active', event_id)
				else:
					self.redis.srem(f'{self.name}:events:{self.league}:active', event_id)

				event_data = {
					'event_key': event_key,
					'league': self.league,
					'start_time': start_time,
					'away': away,
					'home': home,
					'status': status,
				}

				event_hash = generate_data_hash(event_data)
				prev_hash = self.redis.get(f'{self.name}:hashes:{event_key}')
				if prev_hash != event_hash:
					# Event data has changed, cache event and update DB
					events.append(event_data)
					self.redis.set(f'{self.name}:events:{event_key}', json.dumps(event_data), ex=EVENT_EXPIRATION_TIME)
					self.redis.set(f'{self.name}:hashes:{event_key}', event_hash, ex=EVENT_EXPIRATION_TIME)
					self.redis.set(f'{self.name}:keys:{event_id}', event_key, ex=EVENT_EXPIRATION_TIME)
					self.logger.info(f'scraped {event_key}')

			except NormalizationError as e:
				self.logger.warning(f'{e} ({self.league})')
			except Exception as e:
				self.logger.exception(f'{e} occured while scraping events ({self.league})')

		if not events:	
			self.logger.info(f'no new events to upsert ({self.league})')
		else:
			self.logger.info(f'upserting {len(events)} events ({self.league})')
			batch_upsert_events.delay(events)


	def parse_odds(self):
		url = ESPNBET_URLS[self.league]
		if not url:
			self.logger.warning(f'odds url not found ({self.league})')
			return

		self.logger.info(f'starting odds request ({self.league})')
		event_ids = self.redis.smembers(f'{self.name}:events:{self.league}:active')

		odds = []
		for e_id in event_ids:
			try:
				event_url = url + f'/{e_id}/competitions/{e_id}/odds'
				event_key = self.redis.get(f'{self.name}:keys:{e_id}')
				if not event_key:
					continue
				event_data = self.fetch_data(event_url)
				self.logger.info(f'fetched {event_key} odds ({self.league})')
			except Exception as e:
				self.logger.exception(f'{e} occured while yielding schedule request to {url} ({self.league})')
				continue

			try:
				event = json.loads(self.redis.get(f'{self.name}:events:{event_key}'))
				providers = event_data['items']
				
				if event['status'] == 'upcoming' and len(providers) == 1:
					selections = providers[0]
				elif len(providers) > 1:
					selections  = providers	[1]
				else:
					self.logger.info(f'no valid odds provider for {event_key} ({self.league})')
					continue

				markets, outcomes, lines, values = [], [], [], []

				# Spread
				markets.extend(['spread', 'spread'])
				outcomes.extend([event['away'], event['home']])
				lines.extend([
					extract_float(selections['awayTeamOdds']['current']['pointSpread']['american']),
					extract_float(selections['homeTeamOdds']['current']['pointSpread']['american'])
				])
				values.extend([
					selections['awayTeamOdds']['current']['spread']['value'],
					selections['homeTeamOdds']['current']['spread']['value']
				])
				# Moneyline
				markets.extend(['moneyline', 'moneyline'])
				outcomes.extend([event['away'], event['home']])
				lines.extend([None, None])
				values.extend([
					selections['awayTeamOdds']['current']['moneyLine']['value'],
					selections['homeTeamOdds']['current']['moneyLine']['value']
				])
				# Total
				markets.extend(['total', 'total'])
				outcomes.extend(['over', 'under'])
				lines.extend([
					extract_float(selections['current']['total']['american']),
					extract_float(selections['current']['total']['american'])
				])
				values.extend([
					selections['current']['over']['value'],
					selections['current']['under']['value']
				])

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
						self.logger.info(f'scraped {market_key} [{decimal_to_american(values[i])}] for {event_key}')

			except NormalizationError as e:
				self.logger.warning(f'{e}')
			except Exception as e:
				self.logger.exception(f'{e} occured while scraping odds ({self.league})')

		if not odds:
			self.logger.info(f'no new odds to upsert ({self.league})')
		else:
			self.logger.info(f'upserting {len(odds)} odds ({self.league})')
			batch_upsert_odds.delay(odds)