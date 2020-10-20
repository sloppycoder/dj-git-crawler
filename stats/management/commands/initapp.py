import os

from django.core.management.base import BaseCommand
from stats.models import ConfigEntry, Job
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model

DEFAULT_JOBS = [
    {
        "name": "discover",
        "description": "discover new repositories",
    },
    {
        "name": "index_all",
        "description": "index commits from all registered repositories",
    },
    {
        "name": "stats",
        "description": "gather statistics on all commits",
    },
]


class Command(BaseCommand):
    help = "Initialize the application by load ini file into database and create users"

    def handle(self, *args, **options):
        ini_file = os.getenv("CRAWLER_INI", "crawler/crawler.ini")
        ConfigEntry.load("crawler.ini", ini_file)
        assert ConfigEntry.get("crawler.ini") is not None
        print(f"{ini_file} loaded into database")

        self.create_seed_jobs()

        self.create_user("user", "user")
        self.create_user("admin", "admin")

    def create_user(self, username, password):
        user = get_user_model()
        if user.objects.filter(username=username).count() > 0:
            print(f"User {username} already exists")
            return
        try:
            user.objects.create_superuser(username, "user@company.com", password)
            print(f"{username} user created")
        except IntegrityError as e:
            print(f"Can't create user admin, {e}")

    def create_seed_jobs(self):
        for job in DEFAULT_JOBS:
            try:
                Job(**job).save()
            except IntegrityError:
                print(f"job {job['name']} already exists")
