import os
import sys

def main():
    env = os.getenv('DJANGO_ENV', 'dev')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'api.settings.{env}')

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
