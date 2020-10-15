import traceback
from django.db import connection, DatabaseError, IntegrityError


#  This SQL caculate the stats from commit table and populate the
#  AuthorStat table
AUTHSTATS_SQL_1 = """

update stats_authorstat
set
    lines_added = c.lines_added,
    lines_removed = c.lines_removed,
    commit_count = c.commit_count,
    merge_commit_count = c.merge_commit_count
from (
         select stats_id,
                sum(lines_added)                          lines_added,
                sum(lines_removed)                        lines_removed,
                count(stats_commit)                       commit_count,
                sum(case when is_merge then 1 else 0 end) merge_commit_count
         from stats_commit,
              stats_author
         where stats_commit.author_id = stats_author.id
         gro
     ) c
where c.stats_id = stats_authorstat.id

"""

def populdate_author_stats():
    try:
        cur = connection.cursor()
        cur.execute(AUTHSTATS_SQL_1)
    except (DatabaseError, IntegrityError) as e:
        exc = traceback.format_exc()
        print(f"exception in populdate_author_stats => {e}\n{exc}")

