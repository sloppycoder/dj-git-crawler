from configparser import ConfigParser

from django.db import models
from datetime import datetime, timezone

from .utils import is_remote_git_url


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
        conf.read_string(entry.ini)
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

    @staticmethod
    def locate(name: str, email: str, create: bool = True):
        author = Author.objects.filter(email=email).first()
        # create new author if email does not exist
        if author is None:
            if create:
                stats = AuthorStat()
                stats.save()
                author = Author(name=name, email=email, is_alias=False, stats=stats)
                author.save()
                print(f"created new {author}")
            return author
        else:
            # if author is an alias, return the original
            return author.original if author.is_alias else author


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

    def all_commit_hash(self):
        """ return hash of all commits for a repo """
        all_commits = Commit.objects.filter(repo=self).all()
        return dict([(c.sha, c.author.id) for c in all_commits])

    @staticmethod
    def register(name, repo_url, repo_type, gitweb_base_url):
        repo = Repository.objects.filter(name=name).first()
        if repo:
            return repo
        web_url = gitweb_base_url.replace("$name", name) if gitweb_base_url else None
        repo = Repository(
            name=name,
            is_remote=is_remote_git_url(repo_url),
            repo_url=repo_url,
            type=repo_type,
            gitweb_base_url=web_url,
        )
        repo.save()
        print(f"registering new repo {name} => {name}")
        return repo


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


class Job(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=256, unique=True)
