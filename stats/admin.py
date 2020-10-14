from django.contrib import admin
from .models import Author, ConfigEntry, Repository, Commit

admin.site.register(Author)
admin.site.register(ConfigEntry)
admin.site.register(Repository)
admin.site.register(Commit)
