#!/bin/sh
set -e

echo "Waiting for database..."
# Simple retry for Postgres readiness (ignored if using sqlite)
if [ -n "$POSTGRES_HOST" ]; then
  python - <<'PY'
import os, time, sys
import socket
host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
for i in range(30):
    try:
        with socket.create_connection((host, port), timeout=1):
            print("Database is up.")
            sys.exit(0)
    except OSError:
        time.sleep(1)
print("Database not reachable after 30s", file=sys.stderr)
sys.exit(1)
PY
fi

echo "Running migrations..."
python manage.py migrate --noinput

exec "$@"
