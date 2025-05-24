from celery.schedules import crontab
import os

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

SPIDER_BATCH_SIZE = os.getenv('SPIDER_BATCH_SIZE', 10)

broker_url = REDIS_URL
result_backend = REDIS_URL

accept_content = ['json']
task_serializer = 'json'

timezone = 'UTC'
enable_utc = True

beat_schedule = {
    'scrape-schedule-events': {
        'task': 'tasks.scrape_schedule_events',
        'schedule': crontab(minute='*/5'),
    },
    'scrape-sportsbook-events': {
        'task': 'tasks.scrape_sportsbook_events',
        'schedule': crontab(minute='*/5'),
    },
    'dispatch-odds-batches': {
        'task': 'tasks.dispatch_scrape_odds_batches',
        'schedule': 30.0,
        'args': (SPIDER_BATCH_SIZE)
    },
    'cleanup-eligible-events': {
        'task': 'tasks.cleanup_eligible_events',
        'schedule': crontab(minute='*/10'),
    },
}