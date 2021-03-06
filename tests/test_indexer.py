import os
import re

import pytest

from stats.indexer import (
    DEFAULT_CONFIG,
    enumerate_bitbucket_projects,
    enumerate_github_projects,
    enumerate_gitlab_projects,
    index_repository,
    register_git_repositories,
    repositories_for_indexing,
)
from stats.models import Author, ConfigEntry

from .utils import (
    author_count,
    commit_count,
    create_some_commit,
    first_repo,
    repository_count,
)


@pytest.mark.django_db
def test_find_author():
    total = author_count()

    # set create flag to False won't create any author
    dev0 = Author.locate("dev1", "dev1@banana.com", create=False)
    assert dev0 is None
    assert author_count() == total

    # create first author
    dev1 = Author.locate("dev1", "dev1@banana.com")
    assert dev1 is not None
    assert author_count() == total + 1

    dev2 = Author.locate("dev1", "dev1@banana.org")
    assert dev2 is not None
    assert author_count() == total + 2

    # set dev1 to be dev2's parent
    dev2.is_alias = True
    dev2.original = dev1
    dev2.save()

    dev3 = Author.locate("dev1", "dev1@banana.org")
    assert dev3.email == dev1.email

    # cleanup what we created during testing
    dev2.delete()
    dev1.delete()
    assert author_count() == total


@pytest.mark.django_db
def test_index_all_repositories(crawler_conf):
    register_git_repositories(crawler_conf)

    # we should have 1 local repo and
    # at least 1 remote repo on gitlab
    assert repository_count() > 2

    # run the indexing before existing this function when
    # all the database updates will be rolled back
    run_scan_repositories()
    run_index_local_repository()
    run_index_remote_repository()


def test_enumerate_gitlab_projects(crawler_conf):
    projs = enumerate_gitlab_projects(crawler_conf["project.remote"])
    assert len(projs) == 2
    assert "hello" in projs[0].path_with_namespace


@pytest.mark.xfail(raises=KeyError)
def test_enumerate_bitbucket_projects(crawler_conf):
    # this test needs username and access token be present
    # in test.ini to pass
    projs = enumerate_bitbucket_projects(crawler_conf["project.innersource"])
    names = [p["slug"] for p in projs]
    assert len(projs) == 6
    assert "corp-archetype" in names


def test_enumerate_github_projects(crawler_conf):
    projs = enumerate_github_projects(crawler_conf["project.github"])
    names = [p.full_name for p in projs]
    assert len(projs) == 2
    assert "sloppycoder/bank-demo-app" in names


def run_scan_repositories():
    count = 0
    for repo in repositories_for_indexing():
        web_url = repo.gitweb_base_url
        print(f"{repo.name} => {repo.repo_url}, {web_url}")
        assert web_url is not None
        assert "$h" not in web_url
        if re.match(r".*git(hub|lab)\.com/.*", web_url):
            count += 1
    # should be 5 without innersource, add 4 with innersource
    assert count == 5


def run_index_local_repository():
    repo = first_repo(is_remote=False)
    new_commits = index_repository(repo.id)
    records_in_db = commit_count(repo)

    assert records_in_db == new_commits
    assert author_count() == 2

    # create some test commits and only new commits will be indexed
    create_some_commit(repo.repo_url, "d1.txt")
    create_some_commit(repo.repo_url, "d2.asc")

    assert index_repository(repo.id) == 2


def run_index_remote_repository():
    repo = first_repo(is_remote=True)
    new_commits = index_repository(repo.id)
    assert new_commits == 7


@pytest.mark.django_db
def test_index_all():
    """
    run full index use crawler.ini instead of test.ini
    for troubleshooting problems at run time
    """
    if os.getenv("RUN_RUN_RUN") == "run":
        ConfigEntry.load(DEFAULT_CONFIG, "crawler/crawler.ini")
        register_git_repositories()
        for repo in repositories_for_indexing():
            index_repository(repo.id)
