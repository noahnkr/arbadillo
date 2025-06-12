import os

env = os.getenv('DJANGO_ENV', 'dev')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'core.settings.{env}')

from django.core.asgi import get_asgi_application
application = get_asgi_application()
