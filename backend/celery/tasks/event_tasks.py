from ..celery import app
from subprocess import run
from common.constants import SPORTSBOOKS

@app.task
def scrape_schedule():
    run([
        'scrapy', 'crawl', 'schedule'
    ])



@app.task
def scrape_sportsbook_schedule(sportsbook):
    for sportsbook in SPORTSBOOKS:
        run([
            'scrapy', 'crawl', sportsbook,
            '-a', 'mode=schedule',
        ])