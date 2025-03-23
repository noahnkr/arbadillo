import os
import scrapy
import redis
from datetime import datetime

from scraper.common.urls import SCHEDULE_URLS

r = redis.Redis()

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
			_date = table.css(".Table__Title::text").get().strip()

			# Normalize date format
			date = datetime.strptime(_date, "%A, %B %d, %Y").strftime("%Y-%m-%d")
			for row in table.css("tbody.Table__TBODY tr"):
				teams = row.css("span.Table__Team > a:last-child::text").getall()

				# Time column
				_time = row.css("td.date__col a::text").get()

				# If element exists, event is either upcoming or live
				if _time:
					if _time.strip() == "LIVE":
						time = None
						status = "ACTIVE"
					else:
						time = datetime.strptime(_time, "%I:%M %p").strftime("%H:%M")
						status = "UPCOMING"

				# Event has completed
				else:
					time = None
					status = "COMPLETED"

				if len(teams) == 2:
					away = teams[0].strip().replace(" ", "-")
					home = teams[1].strip().replace(" ", "-")

					event_id = f"{league}_{away}@{home}_{date}"
					yield {
						"event_id": event_id,
						"league": league,
						"date": date,
						"away": away,
						"home": home,
						"time": time,
						"status": status,
					}