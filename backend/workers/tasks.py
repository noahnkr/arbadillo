import os
import json
import random
from redis import Redis
from celery import shared_task, chain
from common.constants import LEAGUES, SPORTSBOOKS, SCHEDULE_URLS
from common.utils import launch_spider
from common.logging import configure_logging

logger = configure_logging(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

@shared_task
def scrape_all_events():
    """Scrapes the ESPN schedule followed by each eportsbook's league page."""
    logger.info('Starting task to scrape all events')
    return chain(
        scrape_schedule_events.s(),
        scrape_sportsbook_events.s()
    )


@shared_task
def scrape_schedule_events():
    """Scrapes ESPN schedule and updates Redis and DB."""
    for league in LEAGUES:
        if league in SCHEDULE_URLS.keys():
            logger.info(f'Starting ESPN schedule scraping task | league={league} ')
            launch_spider('schedule', args={'league': league})


@shared_task
def scrape_sportsbook_events():
    """Scrapes league pages on each sportsbook to discover event URLs."""
    for sportsbook in SPORTSBOOKS:
        logger.info(f'Starting sportsbook schedule scraping task | sportsbook={sportsbook}')
        launch_spider(sportsbook, args={'mode': 'schedule'})


@shared_task
def dispatch_scrape_odds_batches(batch_size=10):
    """Pulls eligible event_keys from Redis and dispatches them in batches to be scraped."""
    logger.info(f'Starting odds batch scraping  task | batch_size={batch_size}')
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
    logger.info(f'Starting batch scraping for {sportsbook}')
    launch_spider(sportsbook, args={
        'mode': 'odds',
        'event_keys': json.dumps(event_keys),
    })


@shared_task
def cleanup_eligible_events():
    """Remove events from eligible set if they are no longer active."""
    logger.info(f'Starting cleanup eligible event task')
    active_keys = redis.smembers('schedule:events:active')

    for sportsbook in SPORTSBOOKS:
        redis_key = f'{sportsbook}:events:eligible'
        for event_key in redis.smembers(redis_key):
            if event_key not in active_keys:
                redis.srem(redis_key, event_key)