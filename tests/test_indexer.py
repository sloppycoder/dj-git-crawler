import pytest

from stats.indexer import (
    index_repository,
    locate_author,
    register_git_repositories,
    scan_repositories,
)

from .utils import (
    author_count,
    create_some_commit,
    commit_count,
    first_repo,
    repository_count,
)


@pytest.mark.django_db
def test_find_author():
    total = author_count()

    # set create flag to False won't create any author
    dev0 = locate_author("dev1", "dev1@banana.com", create=False)
    assert dev0 is None
    assert author_count() == total

    # create first author
    dev1 = locate_author("dev1", "dev1@banana.com")
    assert dev1 is not None
    assert author_count() == total + 1

    dev2 = locate_author("dev1", "dev1@banana.org")
    assert dev2 is not None
    assert author_count() == total + 2

    # set dev1 to be dev2's parent
    dev2.is_alias = True
    dev2.original = dev1
    dev2.save()

    dev3 = locate_author("dev1", "dev1@banana.org")
    assert dev3.email == dev1.email

    # cleanup what we created during testing
    dev2.delete()
    dev1.delete()
    assert author_count() == total


@pytest.mark.django_db
def test_register_git_repositories(crawler_conf):
    register_git_repositories(crawler_conf)

    # we should have 1 local repo and
    # at least 1 remote repo on gitlab
    assert repository_count() > 2

    # run the indexing before existing this function when
    # all the database updates will be rolled back
    run_scan_repositories()
    run_index_local_repository()
    run_index_remote_repository()


def run_scan_repositories():
    count = 0
    for repo in scan_repositories():
        print(f"{repo.name} => {repo.repo_url}")
        count += 1
    assert count == 3


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
