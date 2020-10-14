import glob
from configparser import ConfigParser
from datetime import datetime, timedelta
from os.path import expanduser

from django.conf import settings
from django.utils import timezone
from git import InvalidGitRepositoryError, GitCommandError
from gitlab import Gitlab, GitlabGetError
from pydriller import GitRepository, RepositoryMining

from .models import Author, Repository, Commit, ConfigEntry
from .utils import should_ignore_path, is_remote_git_url

DEFAULT_CONFIG = "crawler.ini"


def all_hash_for_repo(repo):
    return dict([(c.sha, c.author.id) for c in Commit.objects.filter(repo=repo).all()])


def register_repository(name, repo_url, repo_type="UNKNOWN") -> Repository:
    repo = Repository.objects.filter(name=name).first()
    if repo is None:
        repo = Repository(
            name=name, is_remote=is_remote_git_url(repo_url), repo_url=repo_url
        )
        print(f"registering new repo {name} => {name}")
    repo.type = repo_type
    repo.save()
    return repo


def register_git_repositories(conf: ConfigParser = None) -> None:
    conf = conf or ConfigEntry.get(DEFAULT_CONFIG)
    assert conf is not None

    gl = Gitlab(settings.GITLAB_URL, private_token=settings.GITLAB_TOKEN)
    for key in [s for s in conf.sections() if s.find("project.") == 0]:
        section = conf[key]
        group, local_path = section.get("group"), section.get("local_path")
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
                    )
            except GitlabGetError as e:
                print(f"gitlab search {group} has some error {e}")
        else:
            for path in glob.glob(f"{local_path}/{xfilter}", recursive=True):
                try:
                    if GitRepository(path).total_commits() > 0:
                        repo_name = key + path.replace(local_path, "")
                        register_repository(
                            name=repo_name, repo_url=path, repo_type=project_type
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
            author = Author(name=name, email=email, is_alias=False)
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

        for commit in RepositoryMining(repo.repo_url).traverse_commits():
            if commit.hash in old_commits:
                continue

            dev = commit.committer
            author = locate_author(name=dev.name, email=dev.email)
            git_commit = Commit(
                sha=commit.hash,
                message=commit.msg,
                author=author,
                repo=repo,
                created_at=commit.committer_date,
            )
            update_commit_stats(git_commit, commit.modifications)
            git_commit.save()
            count += 1
        repo.set_status(status=repo.RepoStatus.READY)
        print(f"Indexed repository {repo.name}")
    except Exception as e:
        print(f"Exception indexing repository {repo.name} => {e}")
        repo.set_status(status=repo.RepoStatus.ERROR, errmsg=str(e))

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
    cut_off = cut_off or timezone.make_aware(datetime.now() - timedelta(minutes=15))
    count = 0
    for repo in Repository.objects.filter(status=status, last_status_at__lt=cut_off):
        count += 1
        yield repo
    print(f"scanned {count} repositories")
