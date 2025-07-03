from dateutil.parser import isoparse

from .base import SportsbookClient

from common.utils.sportsbook_helpers import create_event_key, get_team_key
from common.utils.client import get_browser
from common.exceptions import NormalizationError

class DraftKingsClient(SportsbookClient):
	NAME = 'draftkings'
	BASE_URL = 'https://sportsbook-nash.draftkings.com/api/sportscontent/dkusil/v1'
	LEAGUE_ID_MAP = {
		'mlb': 84240
	}

	def __init__(self, sport, league):
		super().__init__(self.NAME, sport, league)
	
	def _get(self, path):
		url = self.BASE_URL + path
		headers = {
			'origin': 'https://sportsbook.draftkings.com',
			'referer': 'https://sportsbook.draftkings.com',
		}
		return super()._get(url, headers=headers)
	
	def get_events(self):
		league_url = f'/leagues/{self.LEAGUE_ID_MAP[self.league]}'
		data = self._get(league_url)

		events = data.get('events', [])
		self.logger.info(f'Fetched {len(events)} events ({self.league})')

		return events

	def parse_events(self):
		events = self.get_events()
		for event in events:
			try:
				event_id = event['id']

				participants = event['participants']
				away_team = participants[0]['name'] if participants[0]['venueRole'] == 'Away' else participants[1]['name']
				home_team = participants[0]['name'] if participants[0]['venueRole'] == 'Home' else participants[1]['name']
				away_team_key = get_team_key(away_team, self.league)
				home_team_key = get_team_key(home_team, self.league)

				if not away_team_key or not home_team_key:
					self.logger.warning(f'Missing team(s) aliases for {away_team} and/or {home_team} ({self.league})')
					continue

				start_time = isoparse(event['startEventDate'])
				start_date = start_time.strftime('%Y-%m-%d')

				event_key = create_event_key(start_date, away_team_key, home_team_key)
				self.match_espn_key(event_key, event_id)
			
			except NormalizationError as e:
				self.logger.debug(e)
			except Exception as e:
				self.logger.exception(f'An error occured while parsing events ({self.league}): {e}')	

	def get_markets(self, event_key):
		event_id = self.redis.get(f'{self.name}:ids:{self.league}:{event_key}')
		if not event_id:
			self.logger.warning(f'Unknown event id for {event_key} ({self.league})')
			return {}
		event_url = f'/events/{event_id}/categories'
		data = self._get(event_url)

		self.logger.info(f'Fetched {len(data.get("markets", []))} markets ({self.league})')
		return data
	
	def parse_markets(self, event_key):
		market_selections = []
		data = self.get_markets(event_key)

		market_mappings = {}
		markets = data.get('markets', [])
		for market in markets:
			market_id = market['id']
			market_name = market['name']
			market_mappings[market_id] = market_name

		selections = data.get('selections', [])
		for selection in selections:
			try:
				market_id = selection['marketId']
				if market_id not in market_mappings:
					continue

				market_name = market_mappings[market_id]
				outcome_name = selection['label']

				line = selection.get('points')
				value = selection.get('trueOdds')
				status = 'active'
				if not value:
					value = 0
					status = 'suspended'

				participant = selection.get('participants', [None])[0]
				team   = participant['name'] if participant and participant.get('type') == 'Team' else None
				player = participant['name'] if participant and participant.get('type') == 'Player' else None

				selection_data = self.parse_selection(
					event_key, 
					market_name, 
					outcome_name, 
					value=value,
					line=line,
					team=team,
					player=player,
					status=status,
				)
				if self.compare_and_update_selection(selection_data):
					market_selections.append(selection_data)

			except NormalizationError as e:
				self.logger.debug(e)
			except Exception as e:
				self.logger.exception(f'An error occured while parsing markets for {event_key} ({self.league}): {e}')

		return market_selections
	
	def export_markets(self, event_key):
		export_markets = []
		data = self.get_markets(event_key)

		market_mappings = {}
		markets = data.get('markets', [])
		for market in markets:
			market_id = market['id']
			market_name = market['name']
			market_mappings[market_id] = market_name

		selections = data.get('selections', [])
		for selection in selections:
			try:
				market_id = selection['marketId']
				if market_id not in market_mappings:
					continue

				market_name = market_mappings[market_id]
				outcome_name = selection['label']

				line = selection.get('points')

				participant = selection.get('participants', [None])[0]
				team   = participant['name'] if participant and participant.get('type') == 'Team' else None
				player = participant['name'] if participant and participant.get('type') == 'Player' else None

				export_selection = {
					'market_name': market_name,
					'outcome_name': outcome_name,
					'line': line,
					'team': team,
					'player': player,
					'expected': None,
					'expected_exception': None
				}

				try:
					selection_data = self.parse_selection(
						event_key, 
						market_name, 
						outcome_name, 
						line=line,
						team=team,
						player=player,
					).to_dict()

					for key in ['sportsbook', 'league', 'event_key', 'market_key', 'status', 'value', 'collected_at']:
						selection_data.pop(key, None)

					export_selection['expected'] = selection_data
					export_selection['expected_exception'] = False
				except NormalizationError:
					export_selection['expected_exception'] = True

				export_markets.append(export_selection)

			except Exception as e:
				self.logger.exception(f'An error occured while exporting markets for {event_key} ({self.league}): {e}')
		
		return export_markets

		