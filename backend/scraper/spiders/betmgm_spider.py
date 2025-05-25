import scrapy
import json
from datetime import datetime, timedelta
from redis import Redis
from settings import REDIS_HOST, REDIS_PORT
from common.constants import BETMGM_URLS
from common.utils import (
    normalize_team_name, create_event_key, decimal_to_american, 
    current_timestamp, generate_odds_hash, extract_float
)
from common.logging import configure_logging
from items import OddsItem

logger = configure_logging(__name__)

class BetMGMSpider(scrapy.Spider):
    name = 'betmgm'
    domain = 'https://sports.il.betmgm.com'

    def __init__(self, mode=None, event_keys=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.mode = mode
        self.event_keys = json.loads(event_keys) if event_keys  else []


    def start_requests(self):
        logger.info(f'[{self.name}] Starting sportsbook spider | mode={self.mode}')
        if self.mode == 'schedule':
            for league, url in BETMGM_URLS.items():
                if url:
                    yield scrapy.Request(url, callback=self.parse_schedule, meta={'league': league})
        elif self.mode == 'odds':
            for event_key in self.event_keys:
                url = self.redis.hget(f'{self.name}:urls', event_key)
                if url:
                    yield scrapy.Request(url, callback=self.parse_odds, meta={'event_key': event_key})
        else:
            logger.warning(f'[{self.name}] Invalid mode argument | mode={self.mode}')
            raise ValueError('BetMGMSpider requires mode=schedule or mode=odds and appropriate args')


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

        logger.info(f'[{self.name}] Parsing {league} schedule')
        for event in response.css('ms-six-pack-event.grid-event'):
            try:
                info_container = event.css('a.grid-info-wrapper')
                time_container = event.css('ms-event-timer.grid-event-timer')

                href = info_container.attrib.get('href', '').strip()
                if not href:
                    logger.warning(f'[{self.name}] URL not found for event | league={league}')
                    continue

                event_url = f'{self.domain}{href}'
                teams = info_container.css('div.participant::text').getall()
                raw_time = time_container.css('::text').get().strip()

                start_date = self._parse_start_time(raw_time)

                away = normalize_team_name(teams[0], league)
                home = normalize_team_name(teams[1], league)

                event_key = create_event_key(league, start_date, away, home)

                if self.redis.hexists('schedule:events', event_key) and self.redis.sismember('schedule:events:active', event_key):
                    # Mark event as eligible for odds scraping
                    self.redis.sadd(f'{self.name}:events:eligible', event_key)
                    self.redis.hset(f'{self.name}:urls', event_key, event_url)

            except Exception:
                logger.warning(f'[{self.name}] Error occured while parsing event row | league={league}')
                continue


    def parse_odds(self, response):
        event_key = response.meta['event_key']
        logger.info(f'[{self.name}] Parsing odds for {event_key}')

        for market_block in response.css('ms-option-panel.option-panel'):
            block_header = market_block.css('div.option-group-header-title')
            if 'expanded' not in block_header.attrib.get('class', ''):
                continue

            market_title = block_header.css('::text').get()
            option_container = market_block.css('div.option-group-container')

            if 'six-pack-container' in option_container.attrib.get('class', ''):
                yield from self._parse_six_pack_container(option_container, event_key)
                

    def _parse_six_pack_container(self, container, event_key):
        teams = container.css('div.attribute-key span::text').getall()
        if len(teams) != 2:
            return
        
        options = container.css('ms-option')
        if len(options) != 6:
            return

        for i, option in enumerate(options):
            try:
                team = teams[0] if i < 2 else teams[1]
                league = event_key.split(':')[0]
                line_str = option.css('.name::text').get(default='').strip()
                value_str = option.css('.value::text').get(default="").strip()

                pos = i % 3
                # Spread
                if pos == 0:
                    market = 'spread'
                    outcome = normalize_team_name(team, league)
                    line = extract_float(line_str)
                # Total
                elif pos == 1:
                    market = 'total'
                    outcome = 'over' if 'O' in line_str else 'under'
                    line = extract_float(line_str)
                # Moneyline
                else:
                    market = 'moneyline'
                    outcome = normalize_team_name(team, league)
                    line = None # no line for ML

                value = extract_float(value_str)

                odds = OddsItem(
                    event_key=event_key,
                    sportsbook=self.name,
                    market=market,
                    outcome=outcome,
                    line=line,
                    value=value,
                    player=None,
                    prop=None,
                    collected_at=current_timestamp()
                )

                odds_hash = generate_odds_hash(dict(odds))
                prev_odds = self.redis.hget(f'{self.name}:odds:{event_key}', odds_hash)

                if prev_odds is None:
                    # Odds haven't been cached yet, insert row into DB
                    pass
                elif odds_hash != generate_odds_hash(json.loads(prev_odds)):
                    # Odds have changed, update row in DB
                    pass

                # Update odds in hash
                self.redis.hset(f'{self.name}:odds:{event_key}', odds_hash, json.dumps(dict(odds)))

            except Exception:
                continue

            yield odds