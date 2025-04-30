#!/bin/bash
set -e

# Wait for postgres
echo "Waiting for postgres..."
while ! nc -z postgres 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Wait for redis
echo "Waiting for redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis started"

# Create test database if it doesn't exist
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.test" ]; then
  echo "Creating test database if it doesn't exist..."
  PGPASSWORD=$TEST_DB_PASSWORD psql -h postgres -U $TEST_DB_USER -tc "SELECT 1 FROM pg_database WHERE datname = '$TEST_DB_NAME'" | grep -q 1 || PGPASSWORD=$TEST_DB_PASSWORD psql -h postgres -U $TEST_DB_USER -c "CREATE DATABASE $TEST_DB_NAME"
fi

# Apply database migrations
if [ "$RUN_MIGRATIONS" = "true" ] || [ "$DJANGO_SETTINGS_MODULE" = "config.settings.test" ]; then
  echo "Running migrations..."
  python manage.py migrate
fi

# Collect static files if not in test mode
if [ "$DJANGO_SETTINGS_MODULE" != "config.settings.test" ]; then
  python manage.py collectstatic --noinput
fi

# Execute the command
exec "$@" 