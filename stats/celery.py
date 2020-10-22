import os
from datetime import datetime, timedelta

from celery import Celery, chord
from celery.schedules import crontab
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crawler.settings")
app = Celery("stats")

# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, name="discover_repositories")
def discover_repositories_task(self, **kwargs):
    from stats.indexer import register_git_repositories

    register_git_repositories()


@app.task(bind=True, name="index_repository")
def index_repository_task(self, **kwargs):
    from stats.indexer import index_repository

    return index_repository(kwargs["repo_id"])


@app.task(bind=True, name="gather_author_stats")
def gather_author_stats_task(self, group_output):
    from stats.collector import populate_author_stats

    populate_author_stats()


@app.task(bind=True, name="index_all_repositories")
def index_all_repositories_task(self, **kwargs):
    from stats.indexer import repositories_for_indexing

    # chord allows a task to be executed after all
    # tasks ina group has completed
    cut_off = timezone.make_aware(datetime.now() - timedelta(minutes=5))
    chord(
        [
            index_repository_task.s(repo_id=repo.id)
            for repo in repositories_for_indexing(cut_off=cut_off)
        ]
    )(gather_author_stats_task.s())


@app.task(bind=True, name="analyze_all_repositories")
def analyze_all_repositories_task(self, **kwargs):
    from stats.indexer import analyze_all_repositories

    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    analyze_all_repositories(f"tmp/stats_{timestamp}")


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour="*", minute="1,31", day_of_week="*"),
        discover_repositories_task.s(),
    )

    sender.add_periodic_task(
        crontab(hour="*", minute="12", day_of_week="*"),
        index_all_repositories_task.s(),
    )
