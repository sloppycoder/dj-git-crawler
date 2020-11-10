import json
import os

from git import GitCommandError
from pydriller import ModificationType, RepositoryMining

from .utils import should_ignore_path


def get_repo_stats(repo_path):
    repo_stats = {"ext": {}, "base_path": {}, "commits": {}}
    print(f"get stats on repo {repo_path}")

    try:
        for commit in RepositoryMining(repo_path).traverse_commits():
            incr(repo_stats, "commits", "total")

            if commit.merge:
                incr(repo_stats, "commits", "merge")
                continue

            for mod in commit.modifications:
                file_path = mod.new_path
                if file_path is None:
                    file_path = mod.old_path

                if should_ignore_path(mod.filename):
                    continue

                # file at root directory just use "/" as base_path
                base_path = file_path.split("/")[0] if file_path.find("/") > 0 else "/"
                incr(repo_stats, "base_path", base_path)

                _, ext = os.path.splitext(mod.filename)
                incr(repo_stats, "ext", ext)
                incr(repo_stats, "ext", ext, "added", mod.added)
                incr(repo_stats, "ext", ext, "removed", mod.added)

                if mod.change_type not in [
                    ModificationType.ADD,
                    ModificationType.DELETE,
                    ModificationType.MODIFY,
                    ModificationType.RENAME,
                ]:
                    print(
                        f"**** commit {commit.hash} of {repo_path}:{file_path} is weird, "
                        f"change_type = {mod.change_type} ****"
                    )
    except GitCommandError as e:
        print(f"Exception get_repo_stats {repo_path} => {str(e)}\n{e}")

    return repo_stats


def analyze_all_repositories(report_file, conf=None):
    """
    run some stats on file path and extention on local repositories
    to gather data on what files and path should be ignored
    """
    # import here to avoid circular reference
    from .indexer import enumerate_repositories_by_config

    all_stats = {}
    for is_remote, repo_info in enumerate_repositories_by_config(conf):
        repo_path = repo_info["repo_url"]
        if not is_remote:
            all_stats[repo_path] = get_repo_stats(repo_path)
    if report_file and len(report_file) > 3:
        save_stats(all_stats, report_file)
    return all_stats


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


def save_stats(stats, file_name):
    with open(f"{file_name}.json", "w") as f:
        json.dump(stats, f, sort_keys=True, indent=4)

    with open(f"{file_name}.csv", "w") as out_f:
        out_f.write("bucket,repo,key,value\n")
        for k1 in stats.keys():
            for k2 in stats[k1].keys():
                for k3 in stats[k1][k2].keys():
                    for k4 in stats[k1][k2][k3]:
                        path = os.path.basename(k1)
                        line = f"{k2},{path},{k3},{k4},{stats[k1][k2][k3][k4]}"
                        # print(line)
                        out_f.write(line + "\n")


def update_commit_stats(git_commit, modifications):
    # TODO: evaluate how to update the stats carefully
    added, removed, nloc = 0, 0, 0
    for mod in modifications:
        if mod.change_type is None:
            continue
        file_path = mod.old_path or mod.new_path
        if should_ignore_path(file_path):
            continue
        added += mod.added
        removed += mod.removed
        nloc += mod.nloc if mod.nloc is not None else 0
    git_commit.lines_added = added
    git_commit.lines_removed = removed
    git_commit.lines_of_code = nloc
    git_commit.is_merge = added == 0 and removed == 0
    return git_commit
