import json

from .base import OddsClient

from common.utils.strings import extract_float
from common.utils.sportsbook import (
    create_event_key, create_market_key, normalize_market_name, normalize_team_name, format_odds
)
from common.constants.urls import DRAFTKINGS_URLS
from common.constants.sportsbook import ODDS_TTL, PRIMARY_MARKETS
from common.utils.time import utc_to_cst
from common.exceptions import NormalizationError


class DraftKingsClient(OddsClient):

	def __init__(self, league):
		super().__init__('draftkings', league)


	def parse_schedule(self):
		url = DRAFTKINGS_URLS[self.league]
		headers = {
			'origin': 'https://sportsbook.draftkings.com',
			'referer': 'https://sportsbook.draftkings.com',
		}
		data = self.fetch_data(url, headers=headers)

		event_count = len(data.get('events', []))
		self.logger.info(f'fetched {event_count} events ({self.league})')

		if not event_count:
			return

		events = data.get('events', [])
		for event in events:
			try:
				event_id = event['id']

				teams = event['name'].split('@')
				away = normalize_team_name(teams[0], self.league)
				home = normalize_team_name(teams[1], self.league)

				start_time = utc_to_cst(event['startEventDate'])
				start_date = start_time.split('T')[0]

				event_key = create_event_key(self.league, start_date, away, home)
				self.match_espn_key(event_key, event_id)

			except NormalizationError as e:
				self.logger.debug(e)
			except Exception as E:
				self.logger.exception(f'an error occured while scraping events ({self.league}): {e}')

		
	def parse_primary_odds(self, status):
		url = DRAFTKINGS_URLS[self.league]
		headers = {
			'origin': 'https://sportsbook.draftkings.com',
			'referer': 'https://sportsbook.draftkings.com',
		}
		data = self.fetch_data(url, headers=headers)

		market_count = len(data.get('markets', [])) 
		self.logger.info(f'fetched {market_count} markets ({self.league})')

		if not market_count:
			return

		odds = self._parse_markets_and_selections(data, status)
		self.upsert_data(odds)
	

	def parse_props(self, status):
		url = DRAFTKINGS_URLS['event']
		status_keys = self.redis.smembers(f'espn:events:{status}')

		odds = []
		for event_key in status_keys:
			event_id = self.redis.get(f'{self.name}:ids:{event_key}')
			if not event_id:
				self.logger.warning(f'unknown event id for {event_key} ({self.league})')
				continue

			headers = {
				'origin': 'https://sportsbook.draftkings.com',
				'referer': 'https://sportsbook.draftkings.com',
			}
			url += f'/{event_id}/categories'
			data = self.fetch_data(url, headers=headers)

			market_count = len(data.get('markets', [])) 
			self.logger.info(f'fetched {market_count} markets ({self.league})')

			if not market_count:
				continue
			
			odds.extend(self._parse_markets_and_selections(data, status))
		
		self.upsert_data(odds)


	def _parse_markets_and_selections(self, data, status):
		odds = []

		market_mappings = {}
		markets = data.get('markets', [])
		for market in markets:
			try:
				market_id = market['id']
				event_id = market['eventId']
				market_name = market['name']

				market_mappings[market_id] = { 'event_id': event_id, 'market_name': market_name }

			except NormalizationError as e:
				self.logger.debug(e)
			except Exception as e:
				self.logger.exception(f'an error occured while scraping primary markets ({self.league}): {e}')

		status_keys = self.redis.smembers(f'espn:events:{self.league}:{status}')

		selections = data.get('selections', [])
		for selection in selections:
			try:
				market_id = selection['marketId']
				if market_id not in market_mappings.keys():
					continue

				market_data = market_mappings[market_id]

				event_id = market_data['event_id']
				event_key = self.redis.get(f'{self.name}:keys:{event_id}')
				if not event_key or event_key not in status_keys:
					continue

				market_name = market_data['market_name']
				outcome_name = selection['label']

				line = selection.get('points')
				value = selection['trueOdds']

				participant = selection.get('participants', [None])[0]
				team   = participant['name'] if participant and participant.get('type') == 'Team' else None
				player = participant['name'] if participant and participant.get('type') == 'Player' else None

				odds_data = self.parse_selection(
					event_key, 
					market_name, 
					outcome_name, 
					line=line,
					value=value,
					team=team,
					player=player
				)
				self.logger.info(f'name={market_name} | outcome={outcome_name} | line={line} | team={team} | player={player} -> {format_odds(odds_data)}')
				if self.compare_and_update_odds_cache(odds_data):
					odds.append(odds_data)

			except NormalizationError as e:
				self.logger.debug(e)
			except Exception as e:
				self.logger.exception(f'an error occured while scraping primary selections ({self.league}): {e}')

		return odds

	def export_markets(self, event_keys=[]):
		url = DRAFTKINGS_URLS['event']

		markets = {'sportsbook': self.name, 'events': [] }
		for event_key in event_keys:
			event_markets = { 'event_key': event_key, 'markets': []}
			event_id = self.redis.get(f'{self.name}:ids:{event_key}')
			if not event_id:
				continue

			headers = {
				'origin': 'https://sportsbook.draftkings.com',
				'referer': 'https://sportsbook.draftkings.com',
			}
			url += f'/{event_id}/categories'
			data = self.fetch_data(url, headers=headers)

			market_mapping = {}
			seen = set()
			for market in data.get('markets', []):
				market_id = market['id']
				market_name = market['name']
				market_mapping[market_id] = market_name
			
			for selection in data.get('selections', []):
				market_id = selection['marketId']
				if market_id not in market_mapping.keys() or market_id in seen:
					continue

				market_name = market_mapping[market_id]
				outcome = selection['label']
				line = selection.get('points', None)

				if 'participant' in selection.keys():
					value = selection['participant']['name']
					if selection['participant']['type'] == 'team':
						team = normalize_team_name(value, self.league)
						player = None
					else:
						team = None
						player = value
				else:
					player = None
					team = None

				event_markets['markets'].append({
					'name': market_name,
					'outcome': outcome,
					'line': line,
					'team': team,
					'player': player,
                    'expected_outcome': {},
                    'expected_exception': False,
				})
				seen.add(market_id)
			
			markets['events'].append(event_markets)
		
		return markets