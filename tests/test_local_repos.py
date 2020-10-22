from configparser import ConfigParser

from stats.indexer import analyze_all_repositories


def test_local_repos(crawler_conf):
    stats = analyze_all_repositories("", crawler_conf)
    a_stat = next(iter(stats.values()))
    # print(a_stats)
    assert a_stat["base_path"]["Docker"]["count"], 2
    

def local_ini():
    parser = ConfigParser()
    parser.read_string(
        """
[project.local]
local_path = ~/Projects/ktb/next/work
filter =*
type = LOCAL
gitweb_base_url = nothing
"""
    )
    return parser
