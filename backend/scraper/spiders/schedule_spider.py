import scrapy
import json
from datetime import datetime
from redis import Redis
from common.consants import SCHEDULE_URLS
from common.utils import create_event_key, normalize_team_name, current_timestamp
from items import EventItem

class ScheduleSpider(scrapy.Spider):
	name = 'schedule'
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.redis = Redis()


	def start_requests(self):
		for league, url in SCHEDULE_URLS.items():
			if url:
				yield scrapy.Request(url, callback=self.parse, meta={'league': league})


	def parse(self, response):
		league = response.meta['league']

		for table in response.css('div.ResponsiveTable'):
			raw_date = table.css('.Table__Title::text').get()
			if not raw_date:
				continue

			try:
				event_date = datetime.strptime(raw_date.strip(), '%A, %B %d, %Y').date()
			except ValueError:
				continue # Skip unrecognized date formats

			rows = table.css('tbody.Table__TBODY tr')
			for row in rows:
				event = self._parse_row(row, league, event_date)
				if event:
					# Cache event in redis
					redis_key = f'events:{event['event_key']}'
					self.redis.set(redis_key, json.dumps(dict(event)), ex=60 * 60 * 24)

					# Trigger async insert/update
					# update_event_in_db.delay(event)

					yield event


	def _parse_row(self, row, league, date):
		try:
			teams = row.css('span.Table__Team > a:last-child::text').getall()
			if len(teams) != 2:
				return None

			# Format team names
			away = normalize_team_name(teams[0], league)
			home = normalize_team_name(teams[1], league)
		except Exception:
			return None
		event_key = create_event_key(league, away, home, date)

		# Determine start time and status
		raw_time = row.css('td.date__col a::text').get()
		start_time, status = self._parse_start_time(date, raw_time, event_key)

		if start_time is None or status is None:
			return None

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
		redis_key = f'start_time:{event_key}'

		if time_str:
			if time_str.strip().upper() == 'LIVE':
				cached_time = self.redis.get(redis_key)
				start_time = cached_time.decode('utf-8') if cached_time else None
				self.redis.sadd('events:active', event_key)
				status = 'active'
			else:
				try:
					parsed_time = datetime.strptime(time_str.strip(), '%I:%M %p').time()
					combined = datetime.combine(date, parsed_time)
					start_time = combined.strftime('%Y-%m-%dT%H:%M')

					# Check if stored time is different and update if needed
					prev_time = self.redis.get(redis_key)
					if not prev_time or prev_time.decode('utf-8') != start_time:
						self.redis.set(redis_key, start_time, ex=60 * 60 * 24)

					self.redis.sadd('events:active', event_key)
					status = 'upcoming'
				except ValueError:
					return None, None
		else:
			cached_time = self.redis.get(redis_key)
			start_time = cached_time.decode('utf-8') if cached_time else None
			self.redis.srem('events:active', event_key)
			status = 'completed'

		return start_time, status


