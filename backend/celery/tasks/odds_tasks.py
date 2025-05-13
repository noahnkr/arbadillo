import os
from ..celery import app
from common.constants import SPORTSBOOKS
from redis import Redis

REDIS_HOST = os.getenv('REDIS_HOST', 'loalhost')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

redis = Redis(host=REDIS_HOST, port=REDIS_PORT)

@app.task
def scrape_odds_for_event(sportsbook, event_key, url):
    from subprocess import run
    run([
        'scrapy', 'crawl', sportsbook,
        '-a', 'mode=odds',
        '-a', f'event_key={event_key}',
        '-a', f'url={url}'
    ])

@app.task
def scrape_odds():
    for event_key in redis.smembers('events:active'):
        event_key = event_key.decode('utf-8')
        for sportsbook in SPORTSBOOKS:
            url = redis.hget(f'event_urls:{sportsbook}', event_key)
            if url:
                scrape_odds_for_event.delay(sportsbook, event_key, url)
            else:
                pass # Log event not able to be found