import os

from django.core.management.base import BaseCommand
from stats.models import ConfigEntry
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Initialize the application by load ini file into database and create users"

    def handle(self, *args, **options):
        ini_file = os.getenv("CRAWLER_INI", "crawler/crawler.ini")
        ConfigEntry.load("crawler.ini", ini_file)
        assert ConfigEntry.get("crawler.ini") is not None
        print(f"{ini_file} loaded into database")

        self.create_user("user", "user")
        self.create_user("admin", "admin")

    def create_user(self, username, password):
        user = get_user_model()
        if user.objects.get(username="admin") is not None:
            print(f"User {username} already exists")
            return
        try:
            user.objects.create_superuser("admin", "user@company.com", password)
            print("admin user created")
        except IntegrityError as e:
            print(f"Can't create user admin, {e}")
