from django.db import models
from datetime import datetime
import enum


class RepoStatus(enum.Enum):
    Ready = "ready"
    InUse = "in-use"
    Error = "error"
    Disabled = "disabled"


class ConfigEntry(models.Model):
    name = models.CharField(max_length=32, null=False)
    ini = models.TextField

    def __repr__(self):
        return f"""ConfigEntry {self.name}
                {self.ini}
                """


class Author(models.Model):
    name = models.CharField(max_length=64, null=False)
    email = models.CharField(max_length=64, null=False)
    tag1 = models.CharField(max_length=16)
    tag2 = models.CharField(max_length=16)
    tag3 = models.CharField(max_length=16)
    is_alias = models.BooleanField(default=False)
    original = models.ForeignKey("self", null=True, on_delete=models.PROTECT)


class Repository(models.Model):
    REPO_STATUS = (
        ("ready", "Ready"),
        ("inuse", "In-Use"),
        ("error", "Error"),
        ("disabled", "Disabled"),
    )
    name = models.CharField(max_length=512, null=False, unique=True)
    type = models.CharField(max_length=16, null=False, default="UU")
    enabled = models.BooleanField(default=True)
    is_remote = models.BooleanField(default=False)
    http_url = models.CharField(max_length=256)
    ssh_url = models.CharField(max_length=256)
    status = models.CharField(max_length=8, choices=REPO_STATUS)
    last_status_at = models.DateTimeField(default=datetime.fromtimestamp(0))
    last_error = models.CharField(max_length=256)


class Commit(models.Model):
    sha = models.CharField(max_length=20, null=False)
    message = models.CharField(max_length=2048)
    lines_added = models.IntegerField()
    lines_removed = models.IntegerField()
    lines_of_code = models.IntegerField()
    is_merge = models.BooleanField(default=False)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    created_at = models.DateTimeField()
    repo = models.ForeignKey(Repository, on_delete=models.PROTECT)
