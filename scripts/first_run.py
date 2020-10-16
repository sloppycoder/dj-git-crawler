import sys
from stats.models import ConfigEntry
from django.contrib.auth import get_user_model

# load init app config
ConfigEntry.load("crawler.ini", "crawler/crawler.ini")
assert ConfigEntry.get("crawler.ini") is not None

# create super users
try:
    User = get_user_model()
    User.objects.create_superuser("admin", "admin@company.com", "admin")
except Exception as e:
    print("can't create super users")
    print(e)

try:
    User = get_user_model()
    User.objects.create_superuser("user", "user@company.com", "user")
except Exception as e:
    print("can't create super users")
    print(e)


sys.exit(0)
