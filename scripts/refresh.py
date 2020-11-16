# to run this
#
# python manage.py shell < scripts/refresh.py
#

from stats.celery import discover_repositories_task, index_all_repositories_task

result = discover_repositories_task.delay()
_ = [r for r in result.collect()]  # wait for the task to complete
index_all_repositories_task.delay()
