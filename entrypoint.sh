#!/bin/sh

echo secret = $DJANGO_SECRET

echo "Waiting for postgres at $PG_HOST $PG_PORT..."
while ! nc -zv $PG_HOST $PG_PORT; do
  sleep 0.3
done
echo "PostgreSQL started"

python manage.py flush --no-input

if [ "$1" = "migrate" ]; then
  python manage.py migrate
fi

python manage.py initapp

DEBUG_MODE=1
python manage.py runserver 0.0.0.0:8000
