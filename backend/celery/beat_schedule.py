from .celery import app
from celery.schedules import crontab

app.conf.beat_schedule = {
    'collect-scheduled-events': {
        'task': 'tasks.scrape_schedule',
        'schedule': crontab(minute='*/5'),
    },
    'collect-scheduled-sportsbook-events': {
        'task': 'tasks.scrape_sportsbook_schedule',
        'schedule': crontab(minute='*/5'),
    },
    'collect-active-odds': {
        'task': 'tasks.scape_odds',
        'schedule': 30.0,
    },
}