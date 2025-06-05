from celery.schedules import crontab
from . import tasks
import os

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

broker_url = REDIS_URL
result_backend = REDIS_URL

accept_content = ['json']
task_serializer = 'json'

timezone = 'UTC'
enable_utc = True

beat_schedule = {
    'scrape-events': {
        'task': 'workers.tasks.scrape_all_events',
        'schedule': 30.0,
    },
}