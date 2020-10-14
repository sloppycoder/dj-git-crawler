import sys
from stats.models import ConfigEntry
from django.contrib.auth import get_user_model

# load init app config
ConfigEntry.load("crawler.ini", "crawler/crawler.ini")
assert ConfigEntry.get("crawler.ini") is not None

# create superuser
try:
    User = get_user_model()
    User.objects.create_superuser("admin", "admin@company.com", "admin")
except Exception as e:
    print("can't create super user")
    print(e)

sys.exit(0)
