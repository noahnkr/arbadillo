import json
from datetime import datetime, timedelta
from dateutil import tz
from .base import SportsbookClient
from common.constants import ESPN_URLS, ESPNBET_URLS
from common.utils import (
    normalize_team_name, normalize_status_name, create_event_key, create_market_key, 
    utc_to_cst, current_timestamp, generate_event_hash, generate_odds_hash, extract_float,
    format_odds,
)
from common.logging import configure_logging

logger = configure_logging(__name__)

class ESPNClient(SportsbookClient):
    name = 'espn'

    def __init__(self, league):
        super().__init__(league)


    def parse_schedule(self):
        url = ESPN_URLS[self.league]
        if url:
            logger.info(f'({self.name}) starting schedule request | league={self.league}, url={url}')
            try:
                central = tz.gettz('America/Chicago')
                today = datetime.now(tz=central).strftime('%Y%m%d')
                today_data = self.fetch_data(url, params={'dates': today})

                tomorrow = (datetime.now(tz=central) + timedelta(days=1)).strftime('%Y%m%d')
                tomorrow_data = self.fetch_data(url, params={'dates': tomorrow})
            except Exception as e:
                logger.exception(f'({self.name}) {e} occured while yielding schedule request | league={self.league}, url={url}')

            events = today_data['events'] + (tomorrow_data['events'])
            for e in events:
                try:
                    event_id = e['id']

                    start_time = utc_to_cst(e['date'])
                    start_date = start_time.split('T')[0]

                    teams = e['shortName'].split('@')
                    away = normalize_team_name(teams[0], self.league)
                    home = normalize_team_name(teams[1], self.league)

                    event_key = create_event_key(self.league, start_date, away, home)

                    status = normalize_status_name(e['status']['type']['state'])
                    if status in ['upcoming', 'active']:
                        self.redis.sadd(f'{self.name}:events:{self.league}:active', event_id)
                    else:
                        self.redis.srem(f'{self.name}:events:{self.league}:active', event_id)

                    event = {
                        'event_key': event_key,
                        'league': self.league,
                        'start_time': start_time,
                        'away': away,
                        'home': home,
                        'status': status,
                        'collected_at': current_timestamp()
                    }

                    event_hash = generate_event_hash(event)
                    prev_hash = self.redis.hget(f'{self.name}:hashes', event_key)

                    if prev_hash != event_hash:
                        # Event data has changed, cache event and update DB
                        self.redis.hset(f'{self.name}:events', event_key, json.dumps(event))
                        self.redis.hset(f'{self.name}:keys', event_id, event_key)
                        self.redis.hset(f'{self.name}:hashes', event_id, event_hash)
                        logger.info(f'({self.name}) cached event | league={self.league}, event_key={event_key}')

                except Exception as e:
                    logger.exception(f'({self.name}) {e} occured while parsing event | league={self.league}')
        else:
            logger.warning(f'({self.name}) schedule url not found | league={self.league}')


    def parse_odds(self):
        logger.info(f'({self.name}) starting odds request | league={self.league}')
        url = ESPNBET_URLS[self.league]
        if url:
            event_ids = self.redis.smembers(f'{self.name}:events:{self.league}:active')
            for e_id in event_ids:
                try:
                    event_url = url + f'/{e_id}/competitions/{e_id}/odds'
                    event_key = self.redis.hget(f'{self.name}:keys', e_id)
                    event_data = self.fetch_data(event_url)

                    event = json.loads(self.redis.hget(f'{self.name}:events', event_key))
                    providers = event_data['items']
                    
                    if not providers:
                        logger.info(f'({self.name}) no odds avaialable | league={self.league}, event_key={event_key}')
                        continue

                    # Live odds stored in seperate dict
                    selections = providers[0] if event['status'] == 'upcoming' else providers[1]

                    lines = []
                    markets = []
                    outcomes = []
                    lines = []
                    values = []

                    # Spread
                    markets.extend(['spread', 'spread'])
                    outcomes.extend([event['away'], event['home']])
                    lines.extend([
                        extract_float(selections['awayTeamOdds']['current']['pointSpread']['american']),
                        extract_float(selections['homeTeamOdds']['current']['pointSpread']['american'])
                    ])
                    values.extend([
                        selections['awayTeamOdds']['current']['spread']['value'],
                        selections['homeTeamOdds']['current']['spread']['value']
                    ])
                    # Moneyline
                    markets.extend(['moneyline', 'moneyline'])
                    outcomes.extend([event['away'], event['home']])
                    lines.extend([None, None])
                    values.extend([
                        selections['awayTeamOdds']['current']['moneyLine']['value'],
                        selections['homeTeamOdds']['current']['moneyLine']['value']
                    ])
                    # Total
                    markets.extend(['total', 'total'])
                    outcomes.extend(['over', 'under'])
                    lines.extend([
                        extract_float(selections['current']['total']['american']),
                        extract_float(selections['current']['total']['american'])
                    ])
                    values.extend([
                        selections['current']['over']['value'],
                        selections['current']['under']['value']
                    ])

                    for i in range(6):
                        odds = {
                            'event_key': event_key,
                            'sportsbook': self.name,
                            'market': markets[i],
                            'outcome': outcomes[i],
                            'line': lines[i],
                            'value': values[i],
                            'player': None,
                            'prop': None,
                            'collected_at': current_timestamp()

                        }

                        market_key = create_market_key(markets[i], lines[i])
                        self.redis.sadd(f'{self.name}:markets:{event_key}', market_key)

                        odds_hash = generate_odds_hash(odds)
                        prev_hash = self.redis.hget(f'{self.name}:hashes:{event_key}:{market_key}', outcomes[i])
                        if prev_hash != odds_hash:
                            # Odds data have changed, cache odds and update DB
                            self.redis.hset(f'{self.name}:odds:{event_key}:{market_key}', outcomes[i], json.dumps(odds))
                            self.redis.hset(f'{self.name}:hashes:{event_key}:{market_key}', outcomes[i], odds_hash)
                            logger.info(f'({self.name}) cached {format_odds(odds)} | league={self.league}, event_key={event_key}')

                except Exception as e:
                    logger.exception(f'({self.name}) {e} occured while scraping odds | league={self.league}')
        else:
            logger.warning(f'({self.name}) odds url not found | league={self.league}')


