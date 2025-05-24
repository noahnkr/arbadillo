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
python api/manage.py migrate

# Run initial schedule collection task
python api/manage.py shell -c "from workers.tasks import scrape_all_events; scrape_all_events.delay()"

# Start server
python api/manage.py runserver 0.0.0.0:8000
