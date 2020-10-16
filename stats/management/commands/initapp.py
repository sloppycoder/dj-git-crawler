import getpass
from django.core.management.base import BaseCommand, CommandError
from stats.models import ConfigEntry
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Iniitlize the application by load ini file into database and create users"

    def handle(self, *args, **options):
        ConfigEntry.load("crawler.ini", "crawler/crawler.ini")
        assert ConfigEntry.get("crawler.ini") is not None

        self.create_user("user", "user")

        password = getpass.getpass()
        repeat = getpass.getpass(prompt="Password again:")
        if password != repeat:
            raise CommandError("Passwords entered does not match")
        self.create_user("admin", password)

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
