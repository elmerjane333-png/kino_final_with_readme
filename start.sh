#!/bin/bash
set -e
# run migrations if DATABASE_URL present
if [ -n "$DATABASE_URL" ]; then
  echo 'Running flask db upgrade...'
  flask db upgrade || true
fi
echo 'Starting gunicorn with eventlet...'
exec gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:${PORT:-10000}
