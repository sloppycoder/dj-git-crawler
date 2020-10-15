# Generated by Django 3.0.10 on 2020-10-15 05:26

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Author",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=64)),
                ("email", models.CharField(max_length=64)),
                ("tag1", models.CharField(blank=True, max_length=16, null=True)),
                ("tag2", models.CharField(blank=True, max_length=16, null=True)),
                ("tag3", models.CharField(blank=True, max_length=16, null=True)),
                ("is_alias", models.BooleanField(default=False)),
                (
                    "original",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="stats.Author",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AuthorStat",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("lines_added", models.IntegerField(default=0)),
                ("lines_removed", models.IntegerField(default=0)),
                ("commit_count", models.IntegerField(default=0)),
                ("merge_commit_count", models.IntegerField(default=0)),
                (
                    "last_status_at",
                    models.DateTimeField(
                        default=datetime.datetime(1970, 1, 1, 0, 0, tzinfo=utc)
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ConfigEntry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=32)),
                ("ini", models.TextField(null=True)),
            ],
            options={
                "verbose_name": "Config Entry",
                "verbose_name_plural": "Config Entries",
            },
        ),
        migrations.CreateModel(
            name="Repository",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=512, unique=True)),
                ("type", models.CharField(blank=True, max_length=16, null=True)),
                ("enabled", models.BooleanField(default=True)),
                ("is_remote", models.BooleanField(default=False)),
                ("repo_url", models.CharField(max_length=512, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Ready", "Ready"),
                            ("InUse", "Inuse"),
                            ("Error", "Error"),
                        ],
                        default="Ready",
                        max_length=8,
                    ),
                ),
                (
                    "last_status_at",
                    models.DateTimeField(
                        default=datetime.datetime(1970, 1, 1, 0, 0, tzinfo=utc)
                    ),
                ),
                ("last_error", models.TextField(blank=True, null=True)),
                (
                    "last_commit_at",
                    models.DateTimeField(
                        default=datetime.datetime(1970, 1, 1, 0, 0, tzinfo=utc)
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Repositories",
            },
        ),
        migrations.CreateModel(
            name="Commit",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("sha", models.CharField(max_length=40)),
                ("message", models.CharField(max_length=2048)),
                ("lines_added", models.IntegerField()),
                ("lines_removed", models.IntegerField()),
                ("lines_of_code", models.IntegerField()),
                ("is_merge", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField()),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="stats.Author"
                    ),
                ),
                (
                    "repo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="stats.Repository",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="author",
            name="stats",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to="stats.AuthorStat"
            ),
        ),
    ]
