import glob
import traceback
from fnmatch import fnmatch
from configparser import ConfigParser
from datetime import datetime, timedelta
from os.path import expanduser

from git import InvalidGitRepositoryError, GitCommandError
from gitlab import Gitlab, GitlabGetError, GitlabAuthenticationError
from github import Github, BadCredentialsException
from pydriller import GitRepository, RepositoryMining

from .models import Author, Repository, Commit, ConfigEntry, EPOCH_ZERO
from .analyzer import update_commit_stats

DEFAULT_CONFIG = "crawler.ini"


def register_git_repositories(conf: ConfigParser = None) -> None:
    for is_local_repp, params in enumerate_repositories_by_config(conf):
        Repository.register(**params)


def index_repository(repo_id) -> int:
    repo = Repository.objects.get(id=repo_id)
    repo.set_status(status=repo.RepoStatus.INUSE)

    count = 0
    try:
        old_commits = repo.all_commit_hash()
        last_commit_dt = EPOCH_ZERO

        for commit in RepositoryMining(repo.repo_url).traverse_commits():
            if commit.hash in old_commits:
                continue

            commit_dt = commit.committer_date
            if commit_dt > last_commit_dt:
                last_commit_dt = commit_dt
                # print(f"Updating last_commit_dt to {last_commit_dt}")

            dev = commit.committer
            author = Author.locate(name=dev.name, email=dev.email)
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


def enumerate_gitlab_projects(section):
    xfilter = section.get("filter", "*")
    group = section.get("group")
    url = section.get("gitlab_url")
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


def enumerate_github_projects(section):
    xfilter = section.get("filter", "*")
    query = section.get("query")
    token = section.get("access_token")
    try:
        gh = Github(token)
        result = gh.search_repositories(query=query)
        return [proj for proj in result if fnmatch(proj.full_name, xfilter)]
    except BadCredentialsException as e:
        print(f"gitlab search {query} error {type(e)} => {e}")
    except Exception as e:
        print(f"gitlab search {query} error {type(e)} => {e}")
    return []


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
            server_type = section.get("gitserver_type", "github")
            if server_type == "gitlab":
                for proj in enumerate_gitlab_projects(section):
                    params["name"] = proj.path_with_namespace
                    params["repo_url"] = proj.ssh_url_to_repo
                    yield is_local_repo, params
            if server_type == "github":
                for proj in enumerate_github_projects(section):
                    params["name"] = proj.full_name
                    params["repo_url"] = proj.git_url
                    yield is_local_repo, params
