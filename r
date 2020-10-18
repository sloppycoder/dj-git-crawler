#!/bin/bash

if [ "$1" = "b" ]; then
    shift
    docker build -t sloppycoder/git-crawler:v0.5 .
fi

source .env

docker run -it -p 8000:8000 -p 8001:8001 \
  -e PG_HOST=$PG_HOST -e PG_PORT=$PG_PORT \
  -e PG_USERNAME=$PG_USERNAME -e PG_PASSWORD=$PG_PASSWORD \
  -e PG_DATABASE=$PG_DATABASE \
  -e DJANGO_SECRET=$DJANGO_SECRET \
  -e GITLAB_TOKEN=$GITLAB_TOKEN \
  -e KEY_PASSWORD=$KEY_PASSWORD \
  sloppycoder/git-crawler:v0.5 $*

