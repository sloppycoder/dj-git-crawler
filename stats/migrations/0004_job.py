# Generated by Django 3.0.10 on 2020-10-20 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stats", "0003_create_author_stats_view"),
    ]

    operations = [
        migrations.CreateModel(
            name="Job",
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
                ("description", models.CharField(max_length=256, unique=True)),
            ],
        ),
    ]