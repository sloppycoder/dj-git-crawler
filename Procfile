# under hivemind celery worker detects its running under console and try to
# do something funny. use tee to workaround this problem
worker: celery -A stats worker --beat --scheduler django --loglevel=info | tee /dev/null
flower: flower -A stats --port=8001
web: python manage.py runserver 0.0.0.0:8000
