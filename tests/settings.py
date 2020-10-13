import os.path
from crawler.settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        "TEST": {
            # must have this setting in order to preserve
            # the test database. otherwise defaults to ":memory:"
            "NAME": os.path.join(BASE_DIR, "test.sqlite3"),
        },
    }
}
