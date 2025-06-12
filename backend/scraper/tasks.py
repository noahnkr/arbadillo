import json
import subprocess
from celery import shared_task, chain
from common.constants import LEAGUES, SPORTSBOOKS, CLIENT_SCRAPERS
from common.utils import get_client

@shared_task
def launch_spider(spider_name, mode=None, league=None, event_keys=None):
    """Launch a Scrapy spider as a subprocess."""
    cmd = ['scrapy', 'crawl', spider_name, '-a', f'mode={mode}']

    if mode == 'schedule':
        cmd.extend(['-a', f'league={league}'])
    else:
        event_keys = event_keys or []
        cmd.extend(['-a', f'event_keys={json.dumps(event_keys)}'])

    subprocess.Popen(cmd, cwd='/app/scraper/')


@shared_task
def launch_client(client_name, mode=None, league=None):
    """Launch an API client scraper process."""
    client = get_client(client_name, league)
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
    for league in LEAGUES:
        launch_client('espn', mode='schedule', league=league)


@shared_task
def scrape_sportsbook_events():
    """Scrapes league pages on each sportsbook to discover event URLs."""
    for sportsbook in SPORTSBOOKS[1:]: # Skip ESPN
        for league in LEAGUES:
            if sportsbook in CLIENT_SCRAPERS:
                launch_client(sportsbook, mode='schedule', league=league)


@shared_task
def scrape_sportsbook_odds():
    for sportsbook in SPORTSBOOKS:
        if sportsbook in CLIENT_SCRAPERS:
            for league in LEAGUES:
                launch_client.delay(sportsbook, mode='odds', league=league)