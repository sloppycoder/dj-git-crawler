# under hivemind celery worker detects its running under console and try to
# do something funny. use tee to workaround this problem
worker: celery --broker=redis://localhost:6379/0 -A stats worker --beat --scheduler django --concurrency 2 --time-limit=1800 
flower: celery --broker=redis://localhost:6379/0 flower -A stats --port=8001
web: python manage.py runserver 0.0.0.0:8000 
