#!/bin/bash

# Wait for database
echo "Waiting for database..."
while ! nc -z $DJANGO_DB_HOST 5432; do
  sleep 1
done

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 1
done

echo "Database and Redis are ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn on port $PORT..."
exec gunicorn event_project.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --worker-class=sync \
    --worker-connections=1000 \
    --max-requests=10000 \
    --max-requests-jitter=1000 \
    --timeout=120 \
    --access-logfile /app/logs/gunicorn_access.log \
    --error-logfile /app/logs/gunicorn_error.log \
    --log-level info
