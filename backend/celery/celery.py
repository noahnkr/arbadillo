import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'core.settings.{os.getenv('DJANGO_ENV', 'dev')}')

app = Celery('arbadillo')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()