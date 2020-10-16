#!/bin/sh

if [ "$1" = "b" ]; then
    shift
    docker build -t sloppycoder/git-crawler:v0.5 .
fi

docker run -it -p 8000:8000 -p 8001:8001 \
  -e PG_HOST=172.17.0.1 -e PG_PORT=5432 \
  -e PG_USERNAME=gitcrawler -e PG_PASSWORD=gitcrawler \
  -e PG_DATABASE=testdb \
  -e REDIS_URI=redis://172.17.0.1:6379 \
  -e DJANGO_SECRET="40swarz183x%-%ti6v6&28sy6#17g#32$v8#6x9jk43=3vy" \
  -e GITLAB_TOKEN=he14f2qaT4bYD2S5vChy \
  -e DJANGO_HOST=gf63 \
  -e KEY_PASSWORD=$1 \
  sloppycoder/git-crawler:v0.5 $2

