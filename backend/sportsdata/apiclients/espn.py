import json
from datetime import datetime, timedelta
from dateutil import tz

from .base import SportsClient

from common.utils.sportsbook import (
    create_event_key, generate_data_hash, normalize_status_name, normalize_team_name
)
from common.constants.urls import ESPN_URLS
from common.constants.sportsbook import EVENT_TTL, EVENT_STATUSES
from common.utils.time import utc_to_cst
from common.exceptions import NormalizationError

class ESPNClient(SportsClient):
	def __init__(self):
		super().__init__('espn')


	def parse_schedule(self):
		url = ESPN_URLS[self.league]
		central = tz.gettz('America/Chicago')
		today = datetime.now(tz=central).strftime('%Y%m%d')
		today_data = self.fetch_data(url, params={'dates': today})

		tomorrow = (datetime.now(tz=central) + timedelta(days=1)).strftime('%Y%m%d')
		tomorrow_data = self.fetch_data(url, params={'dates': tomorrow})

		event_data = today_data.get('events', []) + tomorrow_data.get('events', [])
		self.logger.info(f'fetched {len(event_data)} events ({self.league})')

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

				status = normalize_status_name(event['status']['type']['state'], is_odds=False)
				self.redis.sadd(f'{self.name}:events:{self.league}:{status}', event_key)
				for s in EVENT_STATUSES:
					if s != status:
						self.redis.srem(f'{self.name}:events:{self.league}:{s}', event_key)

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
					self.redis.set(f'{self.name}:events:{event_key}', json.dumps(event_data), ex=EVENT_TTL)
					self.redis.set(f'{self.name}:hashes:{event_key}', event_hash, ex=EVENT_TTL)
					self.redis.set(f'{self.name}:ids:{event_key}', event_id, ex=EVENT_TTL)
					self.logger.info(f'scraped {event_key} ({self.league})')

			except NormalizationError as e:
				self.logger.warning(e)
			except Exception as e:
				self.logger.exception(f'an error occured while scraping events ({self.league}): {e}')

		self.upsert_events(events)