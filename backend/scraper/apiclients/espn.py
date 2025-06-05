import json
from .base import SportsbookClient
from common.constants import ESPN_URLS
from common.utils import (
    normalize_team_name, normalize_status_name, create_event_key, utc_to_cst,
    current_timestamp, generate_event_hash
)
from common.logging import configure_logging

logger = configure_logging(__name__)

class ESPNClient(SportsbookClient):
    name = 'espn'

    def __init__(self, league=None):
        super().__init__(league)


    def parse_schedule(self):
        url = ESPN_URLS[self.league]
        if url:
            logger.info(f'({self.name}) starting schedule request | league={self.league}, url={url}')
            try:
                data = self.fetch_data(url)
            except Exception as e:
                logger.critical(f'({self.name}) {e.with_traceback()} occured while yielding schedule request | league={self.league}, url={url}')

            dates = data['events']
            for _, events in dates.items():
                for e in events:
                    try:
                        start_time = utc_to_cst(e['date'])
                        start_date = start_time.split('T')[0]

                        for t in e['teams']:
                            if t['isHome']:
                                home = t['name']
                            else:
                                away = t['name']

                        away = normalize_team_name(away, self.league)
                        home = normalize_team_name(home, self.league)

                        event_key = create_event_key(self.league, start_date, away, home)

                        status = normalize_status_name(e['status']['state'])
                        # Update cache of upcoming/active events
                        if status in ['upcoming', 'active']:
                            self.redis.sadd(f'{self.name}:events:active', event_key)
                        else:
                            self.redis.srem(f'{self.name}:events:active', event_key)

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
                        prev_hash = self.redis.get(f'{self.name}:hashes:{event_key}')

                        if prev_hash != event_hash:
                            # Event data has changed, cache event and update DB
                            self.redis.set(f'{self.name}:events:{event_key}', json.dumps(event))
                            self.redis.set(f'{self.name}:hashes:{event_key}', event_hash)
                            logger.info(f'({self.name}) cached event | league={self.league}, event_key={event_key}')

                    except Exception as e:
                        logger.warning(f'({self.name}) {e.with_traceback()} occured while parsing event | league={self.league}')
        else:
            logger.warning(f'({self.name}) url not found | league={self.league}')


    def parse_odds(self):
        logger.warning(f'({self.name}) cannot parse odds for schedule source')