import glob
import traceback
from configparser import ConfigParser
from datetime import datetime, timedelta
from os.path import expanduser

from django.conf import settings
from git import InvalidGitRepositoryError, GitCommandError
from gitlab import Gitlab, GitlabGetError
from pydriller import GitRepository, RepositoryMining

from .models import Author, AuthorStat, Repository, Commit, ConfigEntry, EPOCH_ZERO
from .utils import should_ignore_path, is_remote_git_url

DEFAULT_CONFIG = "crawler.ini"


def all_hash_for_repo(repo):
    return dict([(c.sha, c.author.id) for c in Commit.objects.filter(repo=repo).all()])


def register_repository(
    name, repo_url, repo_type="UNKNOWN", gitweb_base_url=None
) -> Repository:
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
    conf = conf or ConfigEntry.get(DEFAULT_CONFIG)
    assert conf is not None

    gl = Gitlab(settings.GITLAB_URL, private_token=settings.GITLAB_TOKEN)
    for key in [s for s in conf.sections() if s.find("project.") == 0]:
        section = conf[key]
        group = section.get("group")
        local_path = section.get("local_path")
        gitweb_base_url = section.get("gitweb_base_url")
        if local_path and local_path[0] == "~":
            local_path = expanduser(local_path)
        project_type, xfilter = section.get("type", "UNKNOWN"), section.get(
            "filter", "*"
        )
        if local_path is None:
            # remote project, get project info from gitlab
            try:
                for proj in gl.groups.get(group).projects.list(
                    include_subgroups=True, as_list=False
                ):
                    register_repository(
                        name=proj.path_with_namespace,
                        repo_url=proj.ssh_url_to_repo,
                        repo_type=project_type,
                        gitweb_base_url=gitweb_base_url,
                    )
            except GitlabGetError as e:
                print(f"gitlab search {group} has some error {e}")
        else:
            for path in glob.glob(f"{local_path}/{xfilter}", recursive=True):
                try:
                    if GitRepository(path).total_commits() > 0:
                        repo_name = path.replace(local_path, "")
                        register_repository(
                            name=repo_name,
                            repo_url=path,
                            repo_type=project_type,
                            gitweb_base_url=gitweb_base_url,
                        )
                except (InvalidGitRepositoryError, GitCommandError):
                    print(f"skipping non Git path {path}")
                except Exception as e:
                    print(
                        f"got exception when trying to open git repository at {path} => {e}"
                    )


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


def scan_repositories(status=Repository.RepoStatus.READY, cut_off=None):
    # by default set cut_off time to 15 mins before
    cut_off = cut_off or datetime.now().astimezone() - timedelta(minutes=15)
    count = 0
    for repo in Repository.objects.filter(
        status=status, last_status_at__lt=cut_off, enabled=True
    ):
        count += 1
        yield repo
    print(f"scanned {count} repositories")
