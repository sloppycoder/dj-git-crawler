import pytest
import json
import os.path
from configparser import ConfigParser

from pydriller import RepositoryMining, ModificationType
from stats.indexer import enumerate_repositories_by_config


@pytest.mark.skip(reason="no way of currently testing this")
def test_local_repos():
    """
    run some stats on file path and extention on local repositories
    to gather data on what files and path should be ignored
    """
    all_stats = {}
    for is_local, repo_info in enumerate_repositories_by_config(local_ini()):
        repo_path = repo_info["repo_url"]
        all_stats[repo_path] = get_repo_stats(repo_path)
    save_result(all_stats, "tmp/stats_testing")


def get_repo_stats(repo_path):
    repo_stats = {"ext" : {}, "base_path": {}}

    for commit in RepositoryMining(repo_path).traverse_commits():
        if commit.merge:
            continue

        for mod in commit.modifications:
            _, ext = os.path.splitext(mod.filename)
            incr(repo_stats, "ext", ext)
            incr(repo_stats, "ext", ext, "added", mod.added)
            incr(repo_stats, "ext", ext, "removed", mod.added)

            file_path = mod.new_path
            if file_path is None:
                file_path = mod.old_path

            # file at root directory just use "/" as base_path
            base_path = file_path.split("/")[0] if file_path.find("/") > 0 else "/"
            incr(repo_stats, "base_path", base_path)

            if mod.change_type not in [
                ModificationType.ADD,
                ModificationType.DELETE,
                ModificationType.MODIFY,
                ModificationType.RENAME,
            ]:
                print(f"**** commit {commit.hash} of {repo_path}:{file_path} is weird, change_typpe = {mod.change_type} ****")

    return repo_stats


def incr(stats, category, bucket, key="count", by=1):
    try:
        my_dict = stats[category][bucket]
    except KeyError:
        my_dict = {}
        stats[category][bucket] = my_dict

    try:
        my_dict[key] += by
    except KeyError:
        my_dict[key] = by


def local_ini():
    parser = ConfigParser()
    parser.read_string(
        """
[project.local]
local_path = ~/Projects/ktb/next/gitlab/mirrors/backend/channel-api/mobile-travelcards
filter =travelcards-profile.git
type = LOCAL
gitweb_base_url = nothing
"""
    )
    return parser


def save_result(stats, file_name):
    with open(f"{file_name}.json", "w") as f:
        json.dump(stats, f, sort_keys=True, indent=4)

    with open(f"{file_name}.csv", "w") as out_f:
        for k in stats.keys():
            for k2 in stats[k].keys():
                for k3 in stats[k][k2].keys():
                    for k4 in stats[k][k2][k3]:
                        path = os.path.basename(k)
                        line = f"{k2},{path},{k3},{k4},{stats[k][k2][k3][k4]}"
                        print(line)
                        out_f.write(line + "\n")
