import os

from crawler.settings import *  # noqa: F403

if os.getenv("RUN_RUN_RUN", "") != "run":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),  # noqa:F405
            "TEST": {
                # must have this setting in order to preserve
                # the test database. otherwise defaults to ":memory:"
                "NAME": os.path.join(BASE_DIR, "test.sqlite3"),  # noqa: F405
            },
        }
    }
