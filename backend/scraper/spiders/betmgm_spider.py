import scrapy
import json
from redis import Redis
from settings import REDIS_HOST, REDIS_PORT
from common.constants import BETMGM_URLS

class BetMGMSpider(scrapy.Spider):
    name = 'betmgm'

    def __init__(self, mode=None, event_key=None, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT)
        self.mode = mode
        self.event_key = event_key
        self.url = url


    def start_requests(self):
        if self.mode == 'schedule':
            for league, url in BETMGM_URLS:
                if url:
                    yield scrapy.Request(url, callback=self.parse_schedule, meta={'league': league})
        elif self.mode == 'odds':
            yield scrapy.Request(self.url, callback=self.parse_odds, meta={'event_key': self.event_key})
        else:
            raise ValueError('DraftKingsSpider requires mode=schedule or mode=odds and appropriate args')


    def parse_schedule(self, response):
        league = response.meta['league']


    def parse_odds(self, response):
        event_key = response.meta['event_key']


    def _get_event_from_cache(self, event_key):
        raw = self.redis.get(f'events:{event_key}')
        return json.loads(raw) if raw else {}