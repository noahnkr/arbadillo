import os

env = os.getenv('DJANGO_ENV', 'dev')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'core.settings.{env}')

from celery import Celery
from celery_app import config

app = Celery('backend')
app.config_from_object(config)
app.autodiscover_tasks(['scraper', 'core'])