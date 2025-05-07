import os

env = os.getenv('DJANGO_ENV', 'dev')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'core.settings.{env}')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
