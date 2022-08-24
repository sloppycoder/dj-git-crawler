import os

from celery import Celery

# intialize celery
__all__ = ("celery_app",)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crawler.settings")

celery_app = Celery("stats")
# namespace='CELERY' means all celery-related configuration keys
# should have a `CELERY_` prefix.
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()
