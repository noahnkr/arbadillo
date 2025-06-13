import os
from celery import Celery

env = os.getenv('DJANGO_ENV', 'dev')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'core.settings.{env}')

app = Celery('backend')
app.config_from_object( 'django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')