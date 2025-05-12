from celery import Celery

app = Celery('arbadillo')
app.config_from_object('config')
app.autodiscover_tasks(['tasks'])