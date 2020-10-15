from datetime import datetime, timedelta
from django.contrib import admin
from django.contrib import messages
from django.forms import TextInput
from django.utils.html import format_html
from django.db import models
from .models import Author, AuthorStat, ConfigEntry, Repository, Commit


#
# Hack: unregister models from other installed apps
# will replace the manual unregister with some custom admin site
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

#
# End of unregister other models hack
#


@admin.register(ConfigEntry)
class ConfigEntryAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "tag1",
        "tag2",
        "tag3",
        "lines_added",
        "lines_removed",
        "commits",
        "merges",
        "is_alias",
    )
    list_filter = ("is_alias",)
    list_display_links = ("name",)
    list_select_related = ("stats",)
    search_fields = ["name", "email"]
    list_editable = ["tag1", "tag2", "tag3"]
    formfield_overrides = {
        models.CharField: {"widget": TextInput(attrs={"size": "10"})},
    }

    def has_delete_permission(self, request, obj=None):
        return False

    def lines_added(self, obj):
        return obj.stats.lines_added

    def lines_removed(self, obj):
        return obj.stats.lines_added

    def commits(self, obj):
        return obj.stats.commit_count

    def merges(self, obj):
        return obj.stats.commit_count


class LastCommitDateListFilter(admin.SimpleListFilter):
    title = "Last Commit"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "last_commit"

    def lookups(self, request, model_admin):
        return (
            ("mark1", "last 3 days"),
            ("mark2", "last 7 days"),
            ("mark3", "last 30 days"),
            ("mark4", "last 365 days"),
            ("mark5", "it's been a while"),
        )

    def queryset(self, request, queryset):
        mark1 = datetime.now().astimezone() - timedelta(days=3)
        mark2 = datetime.now().astimezone() - timedelta(days=7)
        mark3 = datetime.now().astimezone() - timedelta(days=30)
        mark4 = datetime.now().astimezone() - timedelta(days=365)
        if self.value() == "mark1":
            return queryset.filter(last_commit_at__gt=mark1)
        if self.value() == "mark2":
            return queryset.filter(last_commit_at__gt=mark2)
        if self.value() == "mark3":
            return queryset.filter(last_commit_at__gt=mark3)
        if self.value() == "mark4":
            return queryset.filter(last_commit_at__gt=mark4)
        if self.value() == "mark5":
            return queryset.all()


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    class Meta:
        get_latest_by = "-last_commit_at"

    list_display = (
        "id",
        "name",
        "type",
        "status",
        "enabled",
        "show_git_url",
        "last_commit_at",
    )
    list_filter = ("enabled", "status", "type", "is_remote", LastCommitDateListFilter)
    search_fields = ["name"]
    actions = ["disable_action", "enable_action", "set_ready_action"]
    # the settings below controls inline editing of "type" field
    list_editable = ["type"]
    save_on_top = True
    formfield_overrides = {
        models.CharField: {"widget": TextInput(attrs={"size": "10"})},
    }

    def has_delete_permission(self, request, obj=None):
        return False

    def show_git_url(self, obj):
        url = obj.gitweb_base_url
        if url and len(url) > 50:
            display_url = f"{url[:26]}...{url[-24:]}"
            return format_html(
                "<a href='{url}'>{display_url}</a>", display_url=display_url, url=url
            )
        else:
            return "no link available"

    show_git_url.short_description = "open Git repository"

    def disable_action(self, request, queryset):
        queryset.update(enabled=False)
        messages.success(request, "Selected repositories disabled")

    disable_action.short_description = "Disable indexing on selected repositories"

    def enable_action(self, request, queryset):
        queryset.update(enabled=True)
        messages.success(request, "Selected repositories enabled")

    enable_action.short_description = "Enable indexing selected repositories"

    def set_ready_action(self, request, queryset):
        queryset.update(
            enabled=True,
            status=Repository.RepoStatus.READY,
            last_error=None,
            last_status_at=datetime.now().astimezone(),
        )
        messages.success(request, "Selected repositories reset to Ready status")

    set_ready_action.short_description = "Reset selected repositories status to Ready"


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    class Meta:
        get_latest_by = "-created_at"

    list_display = (
        "show_sha_url",
        "message",
        "lines_added",
        "lines_removed",
        "is_merge",
    )
    list_display_links = ("message",)
    list_select_related = ("repo",)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def show_sha_url(self, obj):
        short_sha = obj.sha[:7]
        url = obj.repo.gitweb_base_url
        if url:
            return format_html(
                "<a href='{url}'>{display_url}</a>",
                display_url=short_sha,
                url=f"{url}/commit/{obj.sha}",
            )
        else:
            return short_sha

    show_sha_url.short_description = "Link to Git"
