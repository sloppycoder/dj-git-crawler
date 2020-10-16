import io
from configparser import ConfigParser

from django.db import models
from datetime import datetime, timezone

EPOCH_ZERO = datetime(1970, 1, 1, tzinfo=timezone.utc)


class ConfigEntry(models.Model):
    class Meta:
        verbose_name = "Config Entry"
        verbose_name_plural = "Config Entries"

    name = models.CharField(max_length=32)
    ini = models.TextField(null=True)

    def __repr__(self):
        return f"""ConfigEntry {self.name}
                {self.ini}
                """

    def __str__(self):
        return f"ConfigEntry [{self.name}]"

    @staticmethod
    def get(name):
        entry = ConfigEntry.objects.filter(name=name).first()
        if entry is None:
            return None
        conf = ConfigParser()
        conf.read_file(io.StringIO(entry.ini))
        return conf

    @staticmethod
    def load(name, ini_file):
        with open(ini_file, "r") as f:
            content = "".join(f.readlines())
        entry = ConfigEntry.objects.filter(name=name).first()
        entry = entry or ConfigEntry(name=name)
        entry.ini = content
        entry.save()
        return entry


class AuthorAndStat(models.Model):
    name = models.CharField(max_length=64)
    email = models.CharField(max_length=64)
    tag1 = models.CharField(max_length=16)
    tag2 = models.CharField(max_length=16)
    tag3 = models.CharField(max_length=16)
    lines_added = models.IntegerField()
    lines_removed = models.IntegerField()
    commit_count = models.IntegerField()
    merge_commit_count = models.IntegerField()

    class Meta:
        verbose_name = "Author and Stat"
        verbose_name_plural = "Authors and Stats"
        managed = False
        db_table = "stats_author_stats_view"
        ordering = ["-commit_count"]

# this model is intended to be readonly from Django
# the updates will be done directly by using SQL
class AuthorStat(models.Model):
    lines_added = models.IntegerField(default=0)
    lines_removed = models.IntegerField(default=0)
    commit_count = models.IntegerField(default=0)
    merge_commit_count = models.IntegerField(default=0)
    last_status_at = models.DateTimeField(default=EPOCH_ZERO)


class Author(models.Model):
    name = models.CharField(max_length=64)
    email = models.CharField(max_length=64)
    tag1 = models.CharField(max_length=16, null=True, blank=True)
    tag2 = models.CharField(max_length=16, null=True, blank=True)
    tag3 = models.CharField(max_length=16, null=True, blank=True)
    is_alias = models.BooleanField(default=False)
    original = models.ForeignKey("self", null=True, on_delete=models.PROTECT)
    stats = models.OneToOneField(AuthorStat, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Repository(models.Model):
    class Meta:
        verbose_name_plural = "Repositories"

    class RepoStatus(models.TextChoices):
        READY = "Ready"
        INUSE = "InUse"
        ERROR = "Error"

    name = models.CharField(max_length=512)
    type = models.CharField(max_length=16, null=True, blank=True)
    enabled = models.BooleanField(default=True)
    is_remote = models.BooleanField(default=False)
    repo_url = models.CharField(max_length=512, null=True)
    gitweb_base_url = models.CharField(max_length=512, null=True)
    status = models.CharField(
        max_length=8, choices=RepoStatus.choices, default=RepoStatus.READY
    )
    last_status_at = models.DateTimeField(default=EPOCH_ZERO)
    last_error = models.TextField(null=True, blank=True)
    last_commit_at = models.DateTimeField(default=EPOCH_ZERO)

    def set_status(self, status, errmsg=None, last_commit_dt=None):
        self.status = status
        self.last_status_at = datetime.now().astimezone()
        self.last_error = errmsg
        if last_commit_dt is not None:
            self.last_commit_at = last_commit_dt
        self.save()


class Commit(models.Model):
    sha = models.CharField(max_length=40)
    message = models.CharField(max_length=2048)
    lines_added = models.IntegerField()
    lines_removed = models.IntegerField()
    lines_of_code = models.IntegerField()
    is_merge = models.BooleanField(default=False)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    created_at = models.DateTimeField()
    repo = models.ForeignKey(Repository, on_delete=models.PROTECT)
