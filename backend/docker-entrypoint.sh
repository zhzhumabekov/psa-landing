#!/bin/sh
# Перед стартом сайта: миграции базы, свежая статика для Caddy, обязательные разделы.
set -e

python manage.py migrate --no-input
python manage.py collectstatic --no-input --clear --verbosity 0
python manage.py setup_site

exec "$@"
