import os

from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crawler.settings")
app = Celery("stats")

# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
    return "OK"


@app.task(bind=True)
def discover_git_projects_task(self):
    from stats import indexer
    from stats.indexer import register_git_projects
    from stats.models import ConfigEntry
    conf = ConfigEntry.get(indexer.DEFAULT_CONFIG)
    register_git_projects(conf)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour="*", minute="*/2", day_of_week="*"), discover_git_projects_task.s()
    )
