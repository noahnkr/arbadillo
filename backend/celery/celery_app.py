from celery import Celery
import os

env = os.getenv('DJANGO_ENV', 'dev')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'core.settings.{env}')

app = Celery('arbadillo')
app.config_from_object('config')
app.autodiscover_tasks(['tasks'])