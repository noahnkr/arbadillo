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
python manage.py makemigrations sportsdata
python manage.py makemigrations oddsdata
python manage.py migrate

# Bootstrap initial data
echo "Triggering bootstrap task..."
celery -A core call core.tasks.bootstrap_initial_data --queue scraping

# Start server
echo "Starting Django..."
python manage.py runserver 0.0.0.0:8000