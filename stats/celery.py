import datetime
import os

from celery import Celery
from celery.schedules import crontab
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crawler.settings")
app = Celery("stats")

# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def discover_repositories_task(self):
    # import any of these at the beginning of the file will
    # get an "Apps aren't loaded yet" error
    from stats.indexer import register_git_repositories

    register_git_repositories()


@app.task(bind=True)
def index_repository_task(self, **kwargs):
    # import any of these at the beginning of the file will
    # get an "Apps aren't loaded yet" error
    from stats.indexer import index_repository

    repo_id = kwargs["repo_id"]
    index_repository(repo_id)


@app.task(bind=True)
def index_all_repositories_task(self):
    # import any of these at the beginning of the file will
    # get an "Apps aren't loaded yet" error
    from stats.indexer import scan_repositories

    cut_off = timezone.make_aware(datetime.now() - datetime.timedelta(minutes=5))
    for repo in scan_repositories(cut_off=cut_off):
        index_repository_task().delay(repo_id=repo.id)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour="*", minute="*/2", day_of_week="*"), discover_repositories_task.s()
    )

    sender.add_periodic_task(
        crontab(hour="*", minute="*/10", day_of_week="*"),
        index_all_repositories_task.s(),
    )
