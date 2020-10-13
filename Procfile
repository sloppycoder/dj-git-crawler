# under hivemind celery worker detects its running under console and try to
# do something funny. use tee to workaround this problem
worker: celery -A repos worker -l info -B | tee /dev/null
flower: flower -A repos --port=8001
web: python manage.py runserver
