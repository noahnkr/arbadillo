echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."

# Wait for PostgreSQL using Python socket
python << END
import socket, time, os

host = os.getenv("POSTGRES_HOST", "db")
port = int(os.getenv("POSTGRES_PORT", 5432))

while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(0.5)
END

echo "PostgreSQL is up. Starting Django..."

# Run database migrations
python manage.py makemigrations scraper
python manage.py makemigrations django_celery_beat
python manage.py migrate

# Trigger initial scraping task
python -c "from scraper.tasks import run_initial_scrape; run_initial_scrape.delay()"

# Start server
python manage.py runserver 0.0.0.0:8000