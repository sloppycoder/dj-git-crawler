from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=64, null=False)
    email = models.CharField(max_length=64, null=False)
    tag1 = models.CharField(max_length=16)
    tag2 = models.CharField(max_length=16)
    tag3 = models.CharField(max_length=16)
    is_alias = models.BooleanField(default=False)
