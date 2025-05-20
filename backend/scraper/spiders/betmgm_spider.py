import scrapy
import json
from datetime import datetime, timedelta
from redis import Redis
from settings import REDIS_HOST, REDIS_PORT
from common.constants import BETMGM_URLS
from common.utils import normalize_team_name, create_event_key

class BetMGMSpider(scrapy.Spider):
    name = 'betmgm'
    domain = 'sports.il.betmgm.com'

    def __init__(self, mode=None, event_key=None, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT)
        self.mode = mode
        self.event_key = event_key
        self.url = url


    def start_requests(self):
        print('Starting BetMGM requsts...')
        if self.mode == 'schedule':
            for league, url in BETMGM_URLS.items():
                if url:
                    yield scrapy.Request(url, callback=self.parse_schedule, meta={'league': league})
        elif self.mode == 'odds':
            yield scrapy.Request(self.url, callback=self.parse_odds, meta={'event_key': self.event_key})
        else:
            raise ValueError('DraftKingsSpider requires mode=schedule or mode=odds and appropriate args')


    def _parse_start_time(self, time_str: str) -> tuple[str, str]:
        now = datetime.now()

        if 'starting' in time_str.lower():
            event_date = now.date()
        elif 'today' in time_str.lower():
            event_date = now.date()
        elif 'tomorrow' in time_str.lower():
            event_date = (now + timedelta(days=1)).date()
        else:
            try:
                time_parts = time_str.strip().split(' ')
                event_date = datetime.strptime(time_parts[0], '%m/%d/%y').date()
            except Exception:
                event_date = now.date()
        
        return datetime.strftime(event_date, '%Y-%m-%d')


    def parse_schedule(self, response):
        league = response.meta['league']

        for event in response.css('ms-six-pack-event.grid-event'):
            try:
                info_container = event.css('a.grid-info-wrapper')
                time_container = event.css('ms-event-timer.grid-event-timer')

                event_url = info_container.attrib['href']
                teams = info_container.css('div.participant::text').getall()
                raw_time = time_container.css('::text').get().strip()

                start_date = self._parse_start_time(raw_time)

                away = normalize_team_name(teams[0], league)
                home = normalize_team_name(teams[1], league)

                event_key = create_event_key(league, away, home, start_date)
                print('Scraped ', event_key)

                self.redis.hset('event_urls:betmgm', event_key, self.domain + event_url)
            except Exception as e:
                print(e)
                continue


    def parse_odds(self, response):
        event_key = response.meta['event_key']