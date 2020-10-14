import glob
from configparser import ConfigParser
from datetime import datetime, timedelta
from os.path import expanduser

from django.conf import settings
from django.utils import timezone
from git import InvalidGitRepositoryError
from gitlab import Gitlab, GitlabGetError
from gitlab.v4.objects import GroupProject
from pydriller import GitRepository, RepositoryMining

from .models import Author, Repository, Commit
from .utils import should_ignore_path

DEFAULT_CONFIG = "crawler.ini"


def all_hash_for_repo(repo):
    return dict([(c.sha, c.author.id) for c in Commit.objects.filter(repo=repo).all()])


def register_remote_repository(proj: GroupProject, repo_type: str) -> Repository:
    repo = Repository.objects.filter(name=proj.path_with_namespace).first()
    if repo is None:
        repo = Repository(
            name=proj.path_with_namespace,
            is_remote=True,
            http_url=proj.http_url_to_repo,
            ssh_url=proj.ssh_url_to_repo,
            type=repo_type,
        )
    else:
        repo.type = repo_type

    repo.save()
    print(f"registered remote repo {proj.name} => {proj.ssh_url_to_repo}")

    return repo


def register_local_repository(path: str, repo_type: str) -> Repository:
    repo = Repository.objects.filter(name=path).first()
    if repo is None:
        repo = Repository(name=path, is_remote=False, type=repo_type)
    else:
        repo.type = repo_type

    repo.save()
    print(f"registered local repo {path}")

    return repo


def register_git_projects(conf: ConfigParser) -> None:
    gl = Gitlab(settings.GITLAB_URL, private_token=settings.GITLAB_TOKEN)
    for key in [s for s in conf.sections() if s.find("project.") == 0]:
        section = conf[key]
        group, local_path = section.get("group"), section.get("local_path")
        if local_path and local_path[0] == "~":
            local_path = expanduser(local_path)
        project_type, xfilter = section.get("type", "UU"), section.get("filter", "*")
        if local_path is None:
            # remote project, get project info from gitlab
            try:
                for proj in gl.groups.get(group).projects.list(
                    include_subgroups=True, as_list=False
                ):
                    register_remote_repository(proj, project_type)
            except GitlabGetError as e:
                print(f"gitlab search {group} has some error {e}")
        else:
            for path in glob.glob(f"{local_path}/{xfilter}", recursive=True):
                try:
                    if GitRepository(path).total_commits() > 0:
                        register_local_repository(path, project_type)
                except InvalidGitRepositoryError:
                    print(f"skipping non Git path {path}")
                except Exception:
                    print(f"skipping invalid repository path {path}")


def locate_author(name: str, email: str, create: bool = True) -> Author:
    layer = 0
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
        layer += 1
        if layer > 10:
            raise Exception("too many alias levels, please simplify the data")
        author = author.original


def index_repository(repo: Repository) -> int:
    if repo is None:
        return 0

    count = 0
    old_commits = all_hash_for_repo(repo)

    repo_url = repo.ssh_url if repo.is_remote else repo.name
    for commit in RepositoryMining(repo_url).traverse_commits():
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


def index_all_repositories() -> None:
    cut_off = datetime.now() - timedelta(minutes=15)
    for repo in Repository.objects.filter(
        Repository.status == Repository.REPO_STATUS.Ready,
        Repository.last_status_at < cut_off,
    ):
        repo_name = repo.name
        print(f"indexing repo {repo_name} ")
        try:
            n = index_repository(repo)
            print(f"indexed repo {repo_name} adding {n} new commits")
        except Exception as e:
            print(f"error when indexing repo {repo_name} => {e}")
            repo.last_error = str(e)

        repo.last_status_at = timezone.make_aware(datetime.now())
