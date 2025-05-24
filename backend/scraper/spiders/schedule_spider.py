import scrapy
import json
from datetime import datetime
from redis import Redis
from settings import REDIS_HOST, REDIS_PORT
from common.constants import SCHEDULE_URLS
from common.utils import create_event_key, normalize_team_name, current_timestamp, generate_events_hash
from items import EventItem

class ScheduleSpider(scrapy.Spider):
	name = 'schedule'
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


	def start_requests(self):
		for league, url in SCHEDULE_URLS.items():
			if url:
				yield scrapy.Request(url, callback=self.parse, meta={'league': league})


	def parse(self, response):
		league = response.meta['league']

		for schedule in response.css('div.ScheduleTables'):
			raw_date = schedule.css('.Table__Title::text').get()
			if not raw_date:
				continue

			try:
				event_date = datetime.strptime(raw_date.strip(), '%A, %B %d, %Y').date()
			except ValueError:
				continue # Skip unrecognized date formats

			for row in schedule.css('tbody.Table__TBODY tr'):
				event = self._parse_row(row, league, event_date.strftime('%Y-%m-%d'))
				if event:
					redis_key = 'schedule:events'
					event_key = event['event_key']
					prev_event = self.redis.hget(redis_key, event_key)

					if prev_event is None:
						# Event hasn't been cached yet, insert row into DB
						pass
					elif generate_events_hash(dict(event)) != generate_events_hash(json.loads(prev_event)): 
						# Event info has changed, update row in DB
						pass
					
					# Update event cache
					self.redis.hset(redis_key, event_key, json.dumps(dict(event)))
					yield event


	def _parse_row(self, row, league, date):
		try:
			teams = row.css('span.Table__Team > a:last-child')
			if len(teams) != 2:
				return None

			# Format team names
			away = normalize_team_name(teams[0].attrib.get('href', '').split('/')[6], league)
			home = normalize_team_name(teams[1].attrib.get('href', '').split('/')[6], league)
		except Exception:
			return None

		event_key = create_event_key(league, date, away, home)

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
            league=league,
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
					return None, None
		else:
			# Time element doesn't exist on page, thus the event must be completed
			start_time = self.redis.get(redis_key)
			status = 'completed'

		return start_time, status


