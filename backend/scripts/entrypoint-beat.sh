set -e
set -x

echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."

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

echo "PostgreSQL is up."

echo "Checking that migrations are applied..."
while true; do
    MIGRATIONS=$(python manage.py showmigrations django_celery_beat | grep '\[X\]' || true)
    if [ -n "$MIGRATIONS" ]; then
        echo "django_celery_beat migrations detected."
        break
    fi
    echo "Migrations not applied yet, waiting..."
    sleep 2
done

echo "Starting Celery Beat..."
exec celery -A core beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
