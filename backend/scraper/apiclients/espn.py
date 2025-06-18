import json
from datetime import datetime, timedelta
from dateutil import tz
from .base import SportsbookClient
from scraper.tasks import batch_upsert_events, batch_upsert_odds
from common.constants.urls import ESPN_URLS, ESPNBET_URLS
from common.constants.sportsbook import (
    EVENT_EXPIRATION_TIME, ODDS_EXPIRATION_TIME, PLAYER_EXPIRATION_TIME, TEAM_EXPIRATION_TIME,
	EVENT_STATUSES,
)
from common.utils import (
	normalize_team_name, normalize_market_name, normalize_status_name, create_event_key, 
	create_market_key, utc_to_cst, generate_data_hash, format_odds,
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

				status = normalize_status_name(event['status']['type']['state'], event=True)
				self.redis.sadd(f'{self.name}:events:{status}', event_key)
				# Remove from other status sets if status has changed
				for s in EVENT_STATUSES:
					if s != status:
						self.redis.srem(f'{self.name}:events:{s}', event_key)

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
					self.redis.set(f'{self.name}:ids:{event_key}', event_id, ex=EVENT_EXPIRATION_TIME)
					self.logger.info(f'scraped {event_key} ({self.league})')

			except NormalizationError as e:
				self.logger.warning(f'{e} ({self.league})')
			except Exception as e:
				self.logger.exception(f'{e} occured while scraping events ({self.league})')

		if not events:	
			self.logger.info(f'no new events to upsert ({self.league})')
		else:
			self.logger.info(f'upserting {len(events)} events ({self.league})')
			batch_upsert_events.delay(events)


	def parse_primary_odds(self, status):
		url = ESPNBET_URLS[self.league]
		if not url:
			self.logger.warning(f'primary odds url not found ({self.league})')
			return

		self.logger.info(f'starting primary odds request ({self.league})')
		keys = self.redis.smembers(f'{self.name}:events:{self.league}:{status}')

		primary = []
		for event_key in keys:
			try:
				event_id = self.redis.get(f'{self.name}:ids:{event_key}')
				if not event_id:
					continue

				event_url = url + f'/{event_id}/competitions/{event_id}/odds'
				event_data = self.fetch_data(event_url)
				self.logger.info(f'fetched {event_key} primary odds ({self.league})')
			except Exception as e:
				self.logger.warning(f'{e} occured while yielding primary odds request to {event_url} for {event_key} ({self.league})')
				continue

			try:
				event_primary = self.parse_event_primary_odds(event_key, event_data)
				primary.extend(event_primary)
			except Exception as e:
				self.logger.exception(f'{e} occured while scraping primary odds for {event_key} ({self.league})')
				continue

		if not primary:
			self.logger.info(f'no new primary odds to upsert ({self.league})')
		else:
			self.logger.info(f'upserting {len(primary)} primary odds ({self.league})')
			batch_upsert_odds.delay(primary)


	def parse_event_primary_odds(self, event_key, event_data) -> list:
		event = json.loads(self.redis.get(f'{self.name}:events:{event_key}'))
		providers = event_data['items']
		
		if event['status'] == 'upcoming' and len(providers) == 1:
			selections = providers[0]
		elif len(providers) > 1:
			selections  = providers	[1]
		else:
			self.logger.warning(f'no valid odds provider for {event_key} ({self.league})')
			return []

		markets, outcomes, lines, values = [], [], [], []

		# Spread
		markets.extend(['spread', 'spread'])
		outcomes.extend([event['away'], event['home']])
		lines.extend([
			float(selections['awayTeamOdds']['current']['pointSpread']['american']),
			float(selections['homeTeamOdds']['current']['pointSpread']['american'])
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
			float(selections['current']['total']['american']),
			float(selections['current']['total']['american'])
		])
		values.extend([
			selections['current']['over']['value'],
			selections['current']['under']['value']
		])

		event_primary = []
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
				'team': None,
				'player': None,
			}

			odds_hash = generate_data_hash(odds_data)
			prev_hash = self.redis.get(f'{self.name}:hashes:{event_key}:{market_key}:{outcomes[i]}')
			if prev_hash != odds_hash:
				# Odds data have changed, cache odds and update DB
				event_primary.append(odds_data)
				self.redis.set(f'{self.name}:odds:{event_key}:{market_key}:{outcomes[i]}', json.dumps(odds_data), ex=ODDS_EXPIRATION_TIME)
				self.redis.set(f'{self.name}:hashes:{event_key}:{market_key}:{outcomes[i]}', odds_hash, ex=ODDS_EXPIRATION_TIME)
				self.logger.info(f'scraped {format_odds(odds_data, markets[i])} for {event_key} ({self.league})')

		
		# Cache url to player prop bets
		prop_url = selections['propBets']['$ref']
		self.redis.set(f'{self.name}:prop_urls:{event_key}', prop_url, ex=EVENT_EXPIRATION_TIME)

		return event_primary

	
	def parse_props(self, status): 
		self.logger.info(f'starting props request ({self.league})')
		keys = self.redis.smembers(f'{self.name}:events:{status}')

		props = []
		for event_key in keys:
			url = self.redis.get(f'{self.name}:prop_urls:{event_key}')
			if not url:
				self.logger.warning(f'prop url not found for {event_key} ({self.league})')
				continue

			try:
				prop_data = self.fetch_data(url, params={'limit': 1000})
				self.logger.info(f'fetched {len(prop_data["items"])} props for {event_key} ({self.league})')
			except Exception as e:
				self.logger.warning(f'{e} occured while yielding prop request to {url} for {event_key} ({self.league})')
				continue

			try:
				event_props = self.parse_event_props(self, event_key, prop_data)
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
		for prop in prop_data['items']:
			try:
				if 'athlete' in prop:
					player_url = prop['athlete']['$ref']
					player_id = player_url.split('/athletes/')[-1].split('?')[0]
					team = None
					player = self.redis.get(f'{self.name}:players:{player_id}')
					# Cache player name if it doesn't exist yet
					if not player:
						player_data = self.fetch_data(player_url)
						player = player_data['fullName']
						self.redis.set(f'{self.name}:players:{player_id}', player, ex=PLAYER_EXPIRATION_TIME)
						self.logger.info(f'scraped player `{player}` ({self.league})')
				elif 'team' in prop:
					team_url = prop['team']['$ref']
					team_id = team_url.split('/teams/')[-1].split('?')[0]
					player = None
					team = self.redis.get(f'{self.name}:teams:{team_id}')
					# Cache player name if it doesn't exist yet
					if not team:
						team_data = self.fetch_data(team_url)
						team = normalize_team_name(team_data['displayName'], self.league)
						self.redis.set(f'{self.name}:teams:{team_id}', team, ex=TEAM_EXPIRATION_TIME)
						self.logger.info(f'scraped team `{team}` ({self.league})')
				else:
					self.logger.warning(f'missing athlete/team prop data for {event_key} ({self.league})')
					continue

				market, market_type, _ = normalize_market_name(prop['type']['name'], self.league)

				line = None
				outcome = None
				value = None

				if market_type == 'moneyline':
					outcome = team
					team = None # redundant
					value = float(prop['odds']['decimal']['value'])
				elif market_type == 'spread':
					line = float(prop['odds']['total']['value'])
					outcome = team
					team = None # redundant
					value = float(prop['odds']['decimal']['value'])
				elif market_type == 'yes_no':
					outcome = 'yes' # default value
					value = float(prop['odds']['decimal']['value'])
				elif market_type in ['total', 'over_under']:
					if 'current' not in prop or not prop.get('current', {}):
						self.logger.warning(f'missing over/under value for {market_type} market ({self.league})')
						continue # Over/Under values not included
					found = False
					for side in ['over', 'under']:
						if side in prop['current']:
							line = float(prop['current']['target']['value'])
							outcome = side
							value = float(prop['current'][side]['value'])
							found = True
							break
					if not found:
						continue

				market_key = create_market_key(market, line, team, player)

				odds_data = {
					'event_key': event_key,
					'market_key': market_key,
					'sportsbook': self.name,
					'market': market,
					'outcome': outcome,
					'line': line,
					'value': value,
					'team': team,
					'player': player,
				}

				odds_hash = generate_data_hash(odds_data)
				prev_hash = self.redis.get(f'{self.name}:hashes:{event_key}:{market_key}:{outcome}')
				if prev_hash != odds_hash:
					# Odds data have changed, cache odds and update DB
					event_props.append(odds_data)
					self.redis.set(f'{self.name}:odds:{event_key}:{market_key}:{outcome}', json.dumps(odds_data), ex=ODDS_EXPIRATION_TIME)
					self.redis.set(f'{self.name}:hashes:{event_key}:{market_key}:{outcome}', odds_hash, ex=ODDS_EXPIRATION_TIME)
					self.logger.info(f'scraped {format_odds(odds_data, market_type)} for {event_key} ({self.league})')

			except NormalizationError as e:
				self.logger.warning(f'{e} ({self.name})')
			except Exception as e:
				self.logger.exception(f'{e} occured while scraping props for {event_key} ({self.league})')
		
		return event_props