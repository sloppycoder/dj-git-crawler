import glob
import re
import traceback
from configparser import ConfigParser
from datetime import datetime, timedelta
from fnmatch import fnmatch
from os.path import expanduser

from atlassian import Bitbucket
from git import GitCommandError, InvalidGitRepositoryError
from github import BadCredentialsException, Github
from gitlab import Gitlab, GitlabAuthenticationError, GitlabGetError
from pydriller import GitRepository, RepositoryMining
from requests import HTTPError

from .analyzer import update_commit_stats
from .models import Author, Commit, ConfigEntry, Repository

DEFAULT_CONFIG = "crawler.ini"


def register_git_repositories(conf: ConfigParser = None) -> None:
    for _, params in enumerate_repositories_by_config(conf):
        Repository.register(**params)


def index_repository(repo_id) -> int:
    repo = Repository.objects.get(id=repo_id)
    repo.set_status(status=repo.RepoStatus.INUSE)

    count = 0
    try:
        old_commits = repo.all_commit_hash()
        last_commit_dt = repo.last_commit_at

        for commit in RepositoryMining(
            repo.repo_url, include_refs=True, include_remotes=True
        ).traverse_commits():
            commit_dt = commit.committer_date
            if commit_dt > last_commit_dt:
                last_commit_dt = commit_dt
                # print(f"Updating last_commit_dt to {last_commit_dt}")

            if commit.hash in old_commits:
                continue

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
        exc = traceback.format_exc()
        print(f"Exception indexing repository {repo.name} => {str(e)}\n{exc}")
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
        print(f"authentication error => {e}")
    except Exception as e:
        print(f"gitlab search {query} error {type(e)} => {e}")
    return []


def enumerate_bitbucket_projects(section):
    xfilter = section.get("filter", "*")
    query = section.get("query")
    url = section.get("bitbucket_url")
    username = section.get("username")
    token = section.get("access_token")
    try:
        result = []
        bb = Bitbucket(url=url, username=username, password=token)
        result = bb.repo_list(project_key=query)
        return [repo for repo in result if fnmatch(repo["slug"], xfilter)]
    except HTTPError as e:
        print(f"HTTPError => {e}")
    except Exception as e:
        print(f"bitbucket repo_list {query} error {type(e)} => {e}")
    return []


def enumerate_repositories_by_config(conf):
    conf = conf or ConfigEntry.get(DEFAULT_CONFIG)
    assert conf is not None

    for key in [s for s in conf.sections() if s.find("project.") == 0]:
        section = conf[key]
        params = {"repo_type": section.get("type", "UNKNOWN")}

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
                        params["gitweb_base_url"] = section.get("gitweb_base_url")
                        yield False, params
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
                    params["gitweb_base_url"] = proj.web_url
                    yield True, params
            elif server_type == "bitbucket":
                for proj in enumerate_bitbucket_projects(section):
                    # bitbucket api returns url in format of
                    # ssh://git@innersource.blah.com/~user/some-stuff.git
                    # transform to git@github.com:user/repo.git
                    # otherwise pydrill can't process it
                    link = [d for d in proj["links"]["clone"] if d["name"] == "ssh"][0]
                    params["name"] = f"{proj['project']['key']}/{proj['slug']}"
                    params["repo_url"] = re.sub(r"^ssh://(.*?)/", r"\1:", link["href"])
                    params["gitweb_base_url"] = proj["links"]["self"][0]["href"]
                    yield True, params
            elif server_type == "github":
                for proj in enumerate_github_projects(section):
                    # github api returns git://github.com/sloppycoder/bank-demo.git
                    # transform to git@github.com:user/repo.git
                    # otherwise pydrill can't process it
                    url = re.sub(r"^(git://)(.*?)/", r"git@\2:", proj.git_url)
                    params["name"] = proj.full_name
                    params["repo_url"] = url
                    params["gitweb_base_url"] = proj.html_url
                    yield True, params
            else:
                print(f"Unknow server_type = {server_type}, why?!")


def active_repos():
    return Repository.objects.filter(enabled=True).exclude(
        status=Repository.RepoStatus.ERROR
    )
