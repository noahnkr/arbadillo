import os
import json
import random
from redis import Redis
from celery import shared_task
from common.constants import LEAGUES, SPORTSBOOKS
from common.utils import launch_spider

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

@shared_task
def scrape_schedule_events():
    """Scrapes ESPN schedule and updates Redis and DB."""
    for league in LEAGUES:
        launch_spider('schedule', args={'league': league})


@shared_task
def scrape_sportsbook_events():
    """Scrapes league pages on each sportsbook to discover event URLs."""
    for sportsbook in SPORTSBOOKS:
        launch_spider(sportsbook, args={'mode': 'schedule'})


@shared_task
def dispatch_scrape_odds_batches(batch_size=10):
    """Pulls eligible event_keys from Redis and dispatches them in batches to be scraped."""
    for sportsbook in SPORTSBOOKS:
        redis_key = f'{sportsbook}:events:eligible'
        all_keys = list(redis.smembers(redis_key))
        random.shuffle(all_keys)

        for i in range(0, len(all_keys), batch_size):
            batch = all_keys[i:i + batch_size]
            scrape_odds_batch.delay(sportsbook, batch)


@shared_task
def scrape_odds_batch(sportsbook, event_keys):
    """Launch a Scrapy spider process for a batch of event odds."""
    launch_spider(sportsbook, args={
        'mode': 'odds',
        'event_keys': json.dumps(event_keys),
    })


@shared_task
def cleanup_eligible_events():
    """Remove events from eligible set if they are no longer active."""
    active_keys = redis.smembers('schedule:events:active')

    for sportsbook in SPORTSBOOKS:
        redis_key = f'{sportsbook}:events:eligible'
        for event_key in redis.smembers(redis_key):
            if event_key not in active_keys:
                redis.srem(redis_key, event_key)