#!/bin/bash

# Wait for database to be ready
python wait-for-db.py

# Apply safe migrations only
echo "Applying safe migrations..."
python manage.py migrate --no-input

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create test users if they don't exist
echo "Creating test users..."
python manage.py create_test_users || true

# Ensure media directory exists and has proper permissions
echo "Setting up media directory..."
mkdir -p /app/media
chmod -R 755 /app/media
chown -R appuser:appuser /app/media

# Ensure staticfiles directory exists and has proper permissions
echo "Setting up staticfiles directory..."
mkdir -p /app/staticfiles
chmod -R 755 /app/staticfiles
chown -R appuser:appuser /app/staticfiles

# Start the server with Gunicorn for production
echo "Starting server with Gunicorn..."
# Use the PORT environment variable if set, otherwise default to 8000
exec gunicorn inventory_management.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 4 --worker-class sync --timeout 60