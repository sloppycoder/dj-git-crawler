# Generated by Django 3.0.10 on 2020-10-20 08:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stats", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorAndStat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('email', models.CharField(max_length=64)),
                ('tag1', models.CharField(max_length=16)),
                ('tag2', models.CharField(max_length=16)),
                ('tag3', models.CharField(max_length=16)),
                ('lines_added', models.IntegerField()),
                ('lines_removed', models.IntegerField()),
                ('commit_count', models.IntegerField()),
                ('merge_commit_count', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Author and Stat',
                'verbose_name_plural': 'Authors and Stats',
                'db_table': 'stats_author_stats_view',
                'ordering': ['-commit_count'],
                'managed': False,
            },
        ),
    ]
