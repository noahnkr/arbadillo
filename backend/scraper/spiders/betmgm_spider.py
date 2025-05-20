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
from items import OddsItem

class BetMGMSpider(scrapy.Spider):
    name = 'betmgm'
    domain = 'https://sports.il.betmgm.com'

    def __init__(self, mode=None, event_key=None, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT)
        self.mode = mode
        self.event_key = event_key
        self.url = url


    def start_requests(self):
        print(f'Starting {self.name} requsts')
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
        print(f'Parsing {self.name} schedule')
        league = response.meta['league']

        for event in response.css('ms-six-pack-event.grid-event'):
            try:
                info_container = event.css('a.grid-info-wrapper')
                time_container = event.css('ms-event-timer.grid-event-timer')

                href = info_container.attrib.get('href', '').strip()
                if not href:
                    continue

                event_url = f'{self.domain}{href}'
                teams = info_container.css('div.participant::text').getall()
                raw_time = time_container.css('::text').get().strip()

                start_date = self._parse_start_time(raw_time)

                away = normalize_team_name(teams[0], league)
                home = normalize_team_name(teams[1], league)

                event_key = create_event_key(league, start_date, away, home)

                print(f'Set {event_key} URL: {event_url}')
                self.redis.hset(f'urls:{self.name}', event_key, event_url)
            except Exception:
                continue


    def parse_odds(self, response):
        event_key = response.meta['event_key']
        print(f'Parsing {self.name} odds for {event_key}')

        for market_block in response.css('ms-option-panel.option-panel'):
            block_header = market_block.css('div.option-group-header-title')
            if 'expanded' not in block_header.attrib.get('class', ''):
                continue

            market_title = block_header.css('::text').get()
            option_container = market_block.css('div.option-group-container')

            print(option_container.attrib.get('class', ''))
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
                print(f'Collected {json.dumps(dict(odds))}')
                self.redis.hset(f'odds:{self.name}:{event_key}', odds_hash, json.dumps(dict(odds)))
            except Exception:
                continue

            yield odds