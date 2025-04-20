import scrapy
import redis
from datetime import datetime

from scraper.common.teams import normalize_team_name
from scraper.common.urls import SCHEDULE_URLS
from scraper.settings import REDIS_HOST, REDIS_PORT

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

class ScheduleSpider(scrapy.Spider):
	name = "schedule"

	def __init__(self, leagues=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.leagues = leagues.split(',')

	def start_requests(self):
		for league in self.leagues:
			url = SCHEDULE_URLS.get(league)
			if url:
				yield scrapy.Request(
					url,
					callback=self.parse,
					meta={"league": league}
				)

	def parse(self, response):
		league = response.meta["league"]
		events = []
		for table in response.css("div.ResponsiveTable"):
			# Locate date from table title
			_date = table.css(".Table__Title::text").get()

			if not _date:
				continue

			# Normalize date format
			date = datetime.strptime(_date.strip(), "%A, %B %d, %Y").date()
			for row in table.css("tbody.Table__TBODY tr"):
				event = self._parse_row(row, league, date)
				events.append(event)
				yield event

		return events


	def _parse_row(self, row, league, date):
		teams = row.css("span.Table__Team > a:last-child::text").getall()
		if len(teams) != 2:
			return None

		away = normalize_team_name(teams[0], league)
		home = normalize_team_name(teams[1], league)
		event_id = f"{league}_{away}@{home}_{date.strftime('%Y-%m-%d')}"
		redis_key = f"start_time:{event_id}"

		# Time element
		_time = row.css("td.date__col a::text").get()

		# If time element exists, event is either upcoming or currently active
		if _time:
			if _time.strip() == "LIVE":
				start_time = r.get(redis_key)
				status = "ACTIVE"
			else:
				time = datetime.strptime(_time, "%I:%M %p").time()
				combined_dt = datetime.combine(date, time)
				start_time = combined_dt.strftime("%Y-%m-%dT%H:%M")
				r.set(redis_key, start_time, ex=60 * 60 * 24) # Cache the starting time for 1 day
				status = "UPCOMING"
		# Otherwise, the event has completed
		else:
			start_time = r.get(redis_key)
			status = "COMPLETED"

		return {
			"event_id": event_id,
			"start_time": start_time,
			"league": league,
			"away": away,
			"home": home,
			"status": status,
		}