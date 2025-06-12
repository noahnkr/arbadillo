from django.conf import settings
from scraper import tasks

broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND

accept_content = settings.CELERY_ACCEPT_CONTENT
task_serializer = settings.CELERY_TASK_SERIALIZER
result_serializer = settings.CELERY_RESULT_SERIALIZER

timezone = settings.CELERY_TIMEZONE
enable_utc = True

beat_schedule = {
    'scrape-events': {
        'task': 'scraper.tasks.scrape_all_events',
        'schedule': 30.0,
    },
}