from configparser import ConfigParser

from stats.analyzer import analyze_all_repositories


def test_local_repos(crawler_conf):
    #  stats = analyze_all_repositories("stats_testing", local_ini())
    stats = analyze_all_repositories("", crawler_conf)
    assert stats is not None


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
