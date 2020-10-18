# under hivemind celery worker detects its running under console and try to
# do something funny. use tee to workaround this problem
worker: celery -A stats worker --beat --scheduler django --concurrency 2 | tee /dev/null
flower: sleep 2; flower -A stats --port=8001
web: sleep 2; python manage.py runserver 0.0.0.0:8000
