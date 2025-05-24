import scrapy
import json
from datetime import datetime
from redis import Redis
from settings import REDIS_HOST, REDIS_PORT
from common.constants import SCHEDULE_URLS
from common.utils import create_event_key, normalize_team_name, current_timestamp, generate_events_hash
from common.logging import configure_logging
from items import EventItem

logger = configure_logging(__name__)

class ScheduleSpider(scrapy.Spider):
	name = 'schedule'
	
	def __init__(self, league=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.league = league
		self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


	def start_requests(self):
		logger.info(f'[{self.name}] Starting schedule spider | league={self.league}')
		url = SCHEDULE_URLS.get(self.league, '')
		if url:
			yield scrapy.Request(url, callback=self.parse)


	def parse(self, response):
		logger.info(f'[{self.name}] Parsing response from: {response.url}')
		for schedule in response.css('div.ScheduleTables'):
			raw_date = schedule.css('.Table__Title::text').get()
			if not raw_date:
				logger.warning(f'[{self.name}] Unable to find date | league={self.league}')
				continue

			try:
				event_date = datetime.strptime(raw_date.strip(), '%A, %B %d, %Y').date()
			except ValueError:
				logger.warning(f'[{self.name}] Error parsing date: {raw_date} | league={self.league}')
				continue # Skip unrecognized date formats

			for row in schedule.css('tbody.Table__TBODY tr'):
				event = self._parse_row(row, event_date.strftime('%Y-%m-%d'))
				if event:
					redis_key = 'schedule:events'
					event_key = event['event_key']
					prev_event = self.redis.hget(redis_key, event_key)

					if prev_event is None:
						# Event hasn't been cached yet, insert row into DB
						# insert_into_db(dict(event)).delay()
						logger.info(f'[{self.name}] Insert event: {json.dumps(dict(event))} into DB | league={self.league}')
					elif generate_events_hash(dict(event)) != generate_events_hash(json.loads(prev_event)): 
						# Event info has changed, update row in DB
						# update_event_in_db(dict(event)).delay()
						logger.info(f'[{self.name}] Updating event: {json.dumps(dict(event))} in DB | league={self.league}')

					# Update event cache
					self.redis.hset(redis_key, event_key, json.dumps(dict(event)))
					logger.info(f'[{self.name}] Cached event: {json.dumps(dict(event))} | league={self.league}')
					yield event
				else:
					logger.warning(f'[{self.name}] Event in row is None | league={self.league}')


	def _parse_row(self, row, date):
		try:
			teams = row.css('span.Table__Team > a:last-child')
			if len(teams) != 2:
				logger.warning(f'[{self.name}] Length of teams != 2 | league={self.league}')
				return None

			# Format team names
			away_str = teams[0].attrib.get('href', '').split('/')[6]
			home_str = teams[1].attrib.get('href', '').split('/')[6]
			away = normalize_team_name(away_str, self.league)
			home = normalize_team_name(home_str, self.league)
		except Exception:
			logger.warning(f'[{self.name}] Error normalizing team names: ({away_str}, {home_str}) | league={self.league}')
			return None

		event_key = create_event_key(self.league, date, away, home)

		# Determine start time and status
		raw_time = row.css('td.date__col a::text').get()
		start_time, status = self._parse_start_time(date, raw_time, event_key)

		# Update cache of upcoming/active events
		if status in ['upcoming', 'active']:
			self.redis.sadd('schedule:events:active', event_key)
		else:
			self.redis.srem('schedule:events:active', event_key)

		return EventItem(
            event_key=event_key,
            league=self.league,
            start_time=start_time,
            away_team=away,
            home_team=home,
            status=status,
			collected_at=current_timestamp()
        )
	

	def _parse_start_time(self, date: datetime, time_str: str, event_key: str) -> tuple[str, str]:
		redis_key = f'schedule:events:{event_key}:start_time'

		if time_str:
			if time_str.strip().upper() == 'LIVE':
				# Start time is not shown on page, we must look it up in cache
				# (note: on initial run, there will be no cached time and thus start_time will be None)
				start_time = self.redis.get(redis_key)
				status = 'active'
			else:
				# Start time is shown on page
				try:
					parsed_time = datetime.strptime(time_str.strip(), '%I:%M %p').time()
					combined = datetime.combine(date, parsed_time)
					start_time = combined.strftime('%Y-%m-%dT%H:%M')

					prev_time = self.redis.get(redis_key)
					if not prev_time or prev_time != start_time:
						# Cached start time either doesn't exist or has changed 
						self.redis.set(redis_key, start_time, ex=60 * 60 * 24)

					status = 'upcoming'
				except ValueError:
					# Exception occured while parsing start time
					logger.warning(f'[{self.name}] Error occured while parsing start time | league={self.league}')
					return None, None
		else:
			# Time element doesn't exist on page, thus the event must be completed
			start_time = self.redis.get(redis_key)
			status = 'completed'

		return start_time, status


