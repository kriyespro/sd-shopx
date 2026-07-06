#!/bin/sh
set -e

# Migrations are NOT run automatically here on purpose (see CLAUDE.md
# migration safety rules) — run them explicitly, see DEPLOY.md.
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60
