import os
import json
import random
import subprocess
from redis import Redis
from celery import shared_task, chain
from api.core.utils import insert_or_update_event, insert_or_update_odds
from common.constants import ( 
    LEAGUES, SPORTSBOOKS, SPIDER_SCRAPERS, CLIENT_SCRAPERS, 
)
from common.logging import configure_logging
from common.utils import get_client

logger = configure_logging(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

@shared_task
def launch_spider(spider_name, mode=None, league=None, event_keys=None):
    """Launch a Scrapy spider as a subprocess."""
    cmd = ['scrapy', 'crawl', spider_name, '-a', f'mode={mode}']

    if mode == 'schedule':
        cmd.extend(['-a', f'league={league}'])
    else:
        event_keys = event_keys or []
        cmd.extend(['-a', f'event_keys={json.dumps(event_keys)}'])

    logger.info(f'launching {spider_name} spider | mode={mode}')
    logger.debug(f'calling cmd {cmd}')
    subprocess.Popen(cmd, cwd='/app/scraper/')


@shared_task
def launch_client(client_name, mode=None, league=None):
    """Launch an API client scraper process."""
    client = get_client(client_name, league)
    logger.info(f'launching {client_name} client | mode={mode}, league={league}')
    if mode == 'schedule':
        client.parse_schedule()
    else:
        client.parse_odds()


@shared_task
def scrape_all_events():
    """Scrapes the ESPN schedule followed by each eportsbook's league page."""
    return chain(
        scrape_schedule_events.s(),
        scrape_sportsbook_events.si(),
        scrape_sportsbook_odds.si()
    ).apply_async()


@shared_task
def scrape_schedule_events():
    """Scrapes ESPN schedule and updates Redis and DB."""
    logger.info('starting ESPN schedule scraping task...')
    for league in LEAGUES:
        launch_client('espn', mode='schedule', league=league)


@shared_task
def scrape_sportsbook_events():
    """Scrapes league pages on each sportsbook to discover event URLs."""
    logger.info('starting sportsbook schedule scraping task...')
    for sportsbook in SPORTSBOOKS[1:]:
        for league in LEAGUES:
            if sportsbook in SPIDER_SCRAPERS:
                launch_spider(sportsbook, mode='schedule', league=league)
            elif sportsbook in CLIENT_SCRAPERS:
                launch_client(sportsbook, mode='schedule', league=league)


@shared_task
def scrape_sportsbook_odds():
    logger.info('starting sportsbook odds scraping task...')
    for sportsbook in SPORTSBOOKS:
        if sportsbook in SPIDER_SCRAPERS:
            dispatch_scrape_odds_batches.delay(sportsbook)
        elif sportsbook in CLIENT_SCRAPERS:
            for league in LEAGUES:
                launch_client.delay(sportsbook, mode='odds', league=league)


@shared_task
def dispatch_scrape_odds_batches(sportsbook, batch_size=10):
    """Pulls eligible event_keys from Redis and dispatches them in batches to be scraped."""
    logger.info(f'starting odds batch dispatching task | sportsbook={sportsbook}, batch_size={batch_size}')
    all_keys = list(redis.smembers(f'{sportsbook}:events'))
    random.shuffle(all_keys)

    for i in range(0, len(all_keys), batch_size):
        batch = all_keys[i:i + batch_size]
        scrape_odds_batch.delay(sportsbook, batch)


@shared_task
def scrape_odds_batch(sportsbook, event_keys):
    """Launch a Scrapy spider process for a batch of event odds."""
    logger.info(f'starting batch odds scraping task | sportsbook={sportsbook}')
    launch_spider(sportsbook, mode='odds', event_keys=event_keys)


@shared_task
def insert_or_update_event(event):
    event = insert_or_update_event(event)
    return event


@shared_task
def insert_or_update_odds(odds):
    odds = insert_or_update_odds(odds)
    return odds


@shared_task
def cleanup_eligible_events():
    """Remove events from eligible set if they are no longer active."""
    logger.info(f'starting cleanup eligible event task')
    active_keys = redis.smembers('schedule:events:active')

    for sportsbook in SPORTSBOOKS:
        redis_key = f'{sportsbook}:events:eligible'
        for event_key in redis.smembers(redis_key):
            if event_key not in active_keys:
                redis.srem(redis_key, event_key)

