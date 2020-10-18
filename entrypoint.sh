#!/bin/sh

# descript private key with a passowrd
if [ ! "$KEY_PASSWORD" = "" ]; then
  cd /root
  mv ssh .ssh
  cd .ssh
  # the encryption was done by using this command
  #  openssl enc -aes-256-cbc -pbkdf2 -salt  -in id_rsa  -out id_rsa.enc -k KEY_PASSWORD
  openssl enc -d -aes-256-cbc -pbkdf2  -in id_rsa.enc  -out id_rsa -k $KEY_PASSWORD
  chmod 600 id_rsa
  cd /
fi
#

echo "Waiting for postgres at $PG_HOST $PG_PORT..."
while ! nc -zv $PG_HOST $PG_PORT; do
  sleep 0.3
done
echo "PostgreSQL started"

if [ "$1" = "migrate" ]; then
  shift
  echo running database migrations
  python manage.py migrate
fi

if [ "$1" = "init" ]; then
  shift
  echo initializing the applicaiton
  python manage.py initapp
fi

if [ ! "$1" = "web" ]; then
  celery -A stats worker --beat --scheduler django --concurrency 2 &
  sleep 2
  flower -A stats --port=8001 &
  sleep 2
fi

gunicorn --workers=2 crawler.wsgi --bind=0.0.0.0:8000