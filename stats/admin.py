from django.contrib import admin
from django.contrib import messages
from .models import Author, ConfigEntry, Repository, Commit
from .utils import tz_aware_now


#
# TODO: replace the manual unregister with some custom admin site
#

# unregister django-celery-results models
from django.contrib.auth.models import Group, User


admin.site.unregister(Group)
admin.site.unregister(User)

# unregister django-celery-results models
from django_celery_results.models import TaskResult

admin.site.unregister(TaskResult)

# unregister django-celery-results models
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)

admin.site.unregister(ClockedSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(PeriodicTask)
admin.site.unregister(SolarSchedule)


class ConfigEntryAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


class AuthorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "is_alias", "tag1", "tag2", "tag3", "original")
    list_filter = ("is_alias", )

    def has_delete_permission(self, request, obj=None):
        return False


def disable_action(self, request, queryset):
    queryset.update(enabled=False)
    messages.success(request, "Selected repositories disabled")


def enable_action(self, request, queryset):
    queryset.update(enabled=True)
    messages.success(request, "Selected repositories enabled")


def set_ready_action(self, request, queryset):
    queryset.update(
        enabled=True,
        status=Repository.RepoStatus.READY,
        last_error=None,
        last_status_at=tz_aware_now(),
    )
    messages.success(request, "Selected repositories reset to Ready status")


class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "status", "enabled", "repo_url", "last_status_at")
    list_filter = ("enabled", "status", "type")
    actions = [disable_action, enable_action, set_ready_action]

    def has_delete_permission(self, request, obj=None):
        return False


class CommitAdmin(admin.ModelAdmin):
    list_display = ("sha", "message", "lines_added", "lines_removed", "is_merge")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(ConfigEntry, ConfigEntryAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Repository, RepositoryAdmin)
admin.site.register(Commit, CommitAdmin)
