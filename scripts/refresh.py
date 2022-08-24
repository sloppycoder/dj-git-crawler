# to run this
#
# python manage.py shell < scripts/refresh.py
#

from stats.tasks import discover_repositories, index_all_repositories

result = discover_repositories.delay()
result.list()
index_all_repositories.delay()
