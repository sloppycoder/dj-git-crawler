import glob
import traceback
from fnmatch import fnmatch
from configparser import ConfigParser
from datetime import datetime, timedelta
from os.path import expanduser, splitext

from git import InvalidGitRepositoryError, GitCommandError
from gitlab import Gitlab, GitlabGetError, GitlabAuthenticationError
from pydriller import GitRepository, RepositoryMining, ModificationType

from .models import Author, AuthorStat, Repository, Commit, ConfigEntry, EPOCH_ZERO
from .utils import should_ignore_path, is_remote_git_url, save_stats

DEFAULT_CONFIG = "crawler.ini"


def all_hash_for_repo(repo):
    return dict([(c.sha, c.author.id) for c in Commit.objects.filter(repo=repo).all()])


def register_repository(name, repo_url, repo_type, gitweb_base_url) -> Repository:
    repo = Repository.objects.filter(name=name).first()
    if repo is None:
        repo = Repository(
            name=name,
            is_remote=is_remote_git_url(repo_url),
            repo_url=repo_url,
            gitweb_base_url=gitweb_base_url,
        )
        print(f"registering new repo {name} => {name}")
    repo.type = repo_type
    if gitweb_base_url:
        repo.gitweb_base_url = gitweb_base_url.replace("$name", repo.name)
    repo.save()
    return repo


def register_git_repositories(conf: ConfigParser = None) -> None:
    for is_local_repp, params in enumerate_repositories_by_config(conf):
        register_repository(**params)


def locate_author(name: str, email: str, create: bool = True) -> Author:
    level = 0
    author = Author.objects.filter(email=email).first()
    # create new author if email does not exist
    if author is None:
        if create:
            stats = AuthorStat()
            stats.save()
            author = Author(name=name, email=email, is_alias=False, stats=stats)
            author.save()
            print(f"created new {author}")
        return author
    # recursion to find the top level author
    while True:
        if author and not author.is_alias:
            return author
        level += 1
        if level > 10:
            raise Exception("too many alias levels, please simplify the data")
        author = author.original


def index_repository(repo_id) -> int:
    repo = Repository.objects.get(id=repo_id)
    repo.set_status(status=repo.RepoStatus.INUSE)

    count = 0
    try:
        old_commits = all_hash_for_repo(repo)
        last_commit_dt = EPOCH_ZERO

        for commit in RepositoryMining(repo.repo_url).traverse_commits():
            if commit.hash in old_commits:
                continue

            commit_dt = commit.committer_date
            if commit_dt > last_commit_dt:
                last_commit_dt = commit_dt
                # print(f"Updating last_commit_dt to {last_commit_dt}")

            dev = commit.committer
            author = locate_author(name=dev.name, email=dev.email)
            git_commit = Commit(
                sha=commit.hash,
                message=commit.msg[:2048],  # some commits has super long message
                author=author,
                repo=repo,
                created_at=commit.committer_date,
            )
            update_commit_stats(git_commit, commit.modifications)
            git_commit.save()
            count += 1
        repo.set_status(status=repo.RepoStatus.READY, last_commit_dt=last_commit_dt)
        print(f"Indexed repository {repo.name}")
    # TODO: need to narrow this down
    except Exception as e:
        print(f"Exception indexing repository {repo.name} => {str(e)}\n{e}")
        exc = traceback.format_exc()
        repo.set_status(status=repo.RepoStatus.ERROR, errmsg=exc)

    return count


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


def repositories_for_indexing(status=Repository.RepoStatus.READY, cut_off=None) -> int:
    # by default set cut_off time to 15 mins before
    cut_off = cut_off or datetime.now().astimezone() - timedelta(minutes=15)
    count = 0
    for repo in Repository.objects.filter(
        status=status, last_status_at__lt=cut_off, enabled=True
    ):
        count += 1
        yield repo
    print(f"scanned {count} repositories")
    return count


def enumerate_repositories_by_config(conf):
    conf = conf or ConfigEntry.get(DEFAULT_CONFIG)
    assert conf is not None

    for key in [s for s in conf.sections() if s.find("project.") == 0]:
        section = conf[key]
        params = {
            "gitweb_base_url": section.get("gitweb_base_url"),
            "repo_type": section.get("type", "UNKNOWN"),
        }

        local_path = section.get("local_path")
        is_local_repo = local_path is not None
        if local_path and local_path[0] == "~":
            local_path = expanduser(local_path)

        if is_local_repo:
            # local repo, just scan the local paths
            xfilter = section.get("filter", "*")
            for path in glob.glob(f"{local_path}/{xfilter}", recursive=True):
                try:
                    if GitRepository(path).total_commits() > 0:
                        repo_name = path.replace(local_path, "")
                        params["name"] = repo_name
                        params["repo_url"] = path
                        yield is_local_repo, params
                except (InvalidGitRepositoryError, GitCommandError):
                    print(f"skipping non Git path {path}")
                except Exception as e:
                    print(f"exception when opening git repository at {path} => {e}")
        else:
            # remote project, get project info from gitlab
            for proj in enumerate_gitlab_projects(section):
                params["name"] = proj.path_with_namespace
                params["repo_url"] = proj.ssh_url_to_repo
                yield is_local_repo, params


def enumerate_gitlab_projects(section):
    xfilter = section.get("filter", "*")
    group = section.get("group")
    url = section.get("gitlab_url", "https://www.gitlab.com")
    token = section.get("gitlab_token")
    ssl_verify = section.get("ssl_verify", "yes") == "yes"
    try:
        gl = Gitlab(url, private_token=token, ssl_verify=ssl_verify)
        projects = gl.groups.get(group).projects.list(
            include_subgroups=True, as_list=False
        )
        return [proj for proj in projects if fnmatch(proj.path_with_namespace, xfilter)]
    except GitlabAuthenticationError:
        print(f"authentication error {url}, {token}, {ssl_verify}")
    except GitlabGetError as e:
        print(f"gitlab search {group} error {type(e)} => {e}")
    return []


def get_repo_stats(repo_path):
    repo_stats = {"ext": {}, "base_path": {}}
    print(f"scanning repo {repo_path}")

    try:
        for commit in RepositoryMining(repo_path).traverse_commits():
            if commit.merge:
                continue

            for mod in commit.modifications:
                file_path = mod.new_path
                if file_path is None:
                    file_path = mod.old_path

                if should_ignore_path(file_path):
                    continue

                _, ext = splitext(mod.filename)
                incr(repo_stats, "ext", ext)
                incr(repo_stats, "ext", ext, "added", mod.added)
                incr(repo_stats, "ext", ext, "removed", mod.added)

                # file at root directory just use "/" as base_path
                base_path = file_path.split("/")[0] if file_path.find("/") > 0 else "/"
                incr(repo_stats, "base_path", base_path)

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
    all_stats = {}
    for is_local, repo_info in enumerate_repositories_by_config(conf):
        repo_path = repo_info["repo_url"]
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
