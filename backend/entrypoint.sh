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

python api/manage.py migrate
python api/manage.py runserver 0.0.0.0:8000
