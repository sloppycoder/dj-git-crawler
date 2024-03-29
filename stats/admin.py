from datetime import datetime, timedelta

from admin_interface.models import Theme
from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.auth.models import Group, User
from django.db import models
from django.forms import TextInput
from django.shortcuts import resolve_url
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.safestring import SafeText
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    SolarSchedule,
)
from django_celery_results.models import TaskResult

from .models import Author, AuthorAndStat, Commit, ConfigEntry, Job, Repository
from .tasks import (
    discover_repositories,
    gather_author_stats,
    index_all_repositories,
    index_repository,
)

#
# Hack: unregister models from other installed apps
# will replace the manual unregister with some custom admin site
#

# unregister django-celery-results models
admin.site.unregister(Group)
admin.site.unregister(User)
# unregister django-celery-results models
admin.site.unregister(TaskResult)

# unregister django-celery-results models
admin.site.unregister(ClockedSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(IntervalSchedule)
#  admin.site.unregister(PeriodicTask)
admin.site.unregister(SolarSchedule)

admin.site.unregister(Theme)


#
# End of unregister other models hack
#

#
# helpers
#
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
            return queryset.filter(last_commit_at__lte=mark4)


#
#  ModelAdmin classes
#
@admin.register(ConfigEntry)
class ConfigEntryAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.username == "admin"


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "tag1",
        "tag2",
        "tag3",
        "is_alias",
    )
    list_filter = ("is_alias", "tag1")
    list_display_links = ("name",)
    search_fields = ["name", "email"]
    list_editable = ["tag1", "tag2", "tag3"]
    formfield_overrides = {
        models.CharField: {"widget": TextInput(attrs={"size": "10"})},
    }

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuthorAndStat)
class AuthorAndStatAdmin(admin.ModelAdmin):
    class Meta:
        get_latest_by = "-commit_count"

    list_display = (
        "name",
        "email",
        "tag1",
        "tag2",
        "tag3",
        "lines_added",
        "lines_removed",
        "commit_count",
        "merge_commit_count",
        "commits",
    )
    list_filter = ("tag1", "tag2", "tag3")
    search_fields = ["name", "email"]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def commits(self, obj):
        url = resolve_url(admin_urlname(Commit._meta, SafeText("changelist")))
        url += SafeText(f'?{urlencode({"q":obj.email})}')
        return format_html('<a href="{}">{}</a>', url, "link")


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    class Meta:
        get_latest_by = "-last_commit_at"

    list_display = (
        "id",
        "name",
        "tag1",
        "tag2",
        "tag3",
        "status",
        "enabled",
        "show_git_url",
        "last_commit_at",
        "last_status_at",
    )
    list_filter = (
        "enabled",
        "status",
        "tag1",
        "tag2",
        "tag3",
        "is_remote",
        LastCommitDateListFilter,
    )
    search_fields = ["id", "name"]
    actions = [
        "disable_action",
        "enable_action",
        "set_ready_action",
        "scan_action",
    ]
    # the settings below controls inline editing of "type" field
    list_editable = ["tag1", "tag2", "tag3"]
    save_on_top = True

    formfield_overrides = {
        models.CharField: {"widget": TextInput(attrs={"size": "10"})},
    }

    def has_delete_permission(self, request, obj=None):
        return False

    def show_git_url(self, obj):
        url = obj.gitweb_base_url
        if not url:
            return "no link available"
        display_url = f"{url[:26]}...{url[-24:]}" if len(url) > 50 else url
        return format_html(
            "<a href='{url}'>{display_url}</a>", display_url=display_url, url=url
        )

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

    def scan_action(self, request, queryset):
        for repo in queryset.all():
            index_repository.delay(repo_id=repo.id)
        messages.success(request, "Selected repositories will be scanned shortly")

    scan_action.short_description = "Scan the selected repositories"


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    class Meta:
        get_latest_by = "-created_at"

    list_display = (
        "repo_name",
        "message",
        "author_url",
        "lines_added",
        "lines_removed",
        "created_at",
        "sha_url",
    )
    list_display_links = ("message",)
    list_select_related = ("repo", "author")
    list_filter = ("repo__type", "author__tag1")
    search_fields = ["author__name", "author__email", "repo__name"]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def repo_name(self, obj):
        name = obj.repo.name
        # the last bit of the name after the rightmost "/"
        return name[name.rfind("/") + 1 :]

    def author_url(self, obj):
        author = obj.author if not obj.author.is_alias else obj.author.original
        view = admin_urlname(AuthorAndStat._meta, SafeText("change"))
        url = resolve_url(view, author.id)
        return format_html('<a href="{}">{}</a>', url, str(author))

    def sha_url(self, obj):
        short_sha = obj.sha[:7]
        base_url = obj.repo.gitweb_base_url
        if not base_url:
            return short_sha
        if obj.repo.is_remote:
            url = f"{base_url}/commit/{obj.sha}"
            # hack: bitbucket url ends with /browse, we need to remove it before adding
            url = url.replace("browse/commit", "commits")
        else:
            # url served by gitweb
            url = f"{base_url};a=commit;h={obj.sha}"
        return format_html(
            "<a href='{url}'>{display_url}</a>",
            display_url=short_sha,
            url=url,
        )

    sha_url.short_description = "Link to Git"


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    list_display_links = None
    actions = ["run_job"]

    def has_delete_permission(self, request, obj=None):
        return False

    def run_job(self, request, queryset):
        for job in queryset.all():
            if job.name == "discover":
                discover_repositories.delay()
                messages.success(request, "discover repository job will start shortly")
            elif job.name == "index_all":
                index_all_repositories.delay()
                messages.success(
                    request, "index all repositories job will start shortly"
                )
            elif job.name == "stats":
                gather_author_stats.delay([])
                messages.success(request, "gather statistics job will start shortly")
            else:
                messages.info(request, f"doesn't know what job to run for {job.name}")

    run_job.short_description = "run selected job"
