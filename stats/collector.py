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
        select
            case
                when author.is_alias then original.stats_id
                else author.stats_id
            end statsid,
            sum(lines_added)                          lines_added,
            sum(lines_removed)                        lines_removed,
            count(stats_commit)                       commit_count,
            sum(case when is_merge then 1 else 0 end) merge_commit_count
        from stats_commit
        join stats_author author on (author_id = author.id)
        left outer join  stats_author original on (author.original_id = original.id)
        group by statsid
     ) c
where c.statsid = stats_authorstat.id

"""


def populate_author_stats():
    try:
        cur = connection.cursor()
        cur.execute(AUTHSTATS_SQL_1)
    except (DatabaseError, IntegrityError) as e:
        exc = traceback.format_exc()
        print(f"exception in populdate_author_stats => {e}\n{exc}")
