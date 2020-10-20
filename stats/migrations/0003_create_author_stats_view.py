from django.db import migrations

VIEW_SQL = """
create view stats_author_stats_view
as
    select stats_author.id id, name, email, tag1, tag2, tag3,
           lines_added, lines_removed, commit_count, merge_commit_count
    from stats_author inner join stats_authorstat
        on stats_id = stats_authorstat.id
"""


class Migration(migrations.Migration):

    dependencies = [
        ("stats", "0002_authorandstat"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[(VIEW_SQL, [])],
            reverse_sql=[("drop view stats_author_stats_view;", [])],
        ),
    ]
