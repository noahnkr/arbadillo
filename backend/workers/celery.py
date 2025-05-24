from celery import Celery
import os

env = os.getenv('DJANGO_ENV', 'dev')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'api.core.settings.{env}')

app = Celery('arbadillo')
app.config_from_object('workers.config')
app.autodiscover_tasks(['workers'])