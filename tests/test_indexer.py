import pytest
from pydriller import GitRepository

from stats.indexer import (
    first_repo,
    locate_author,
    register_git_projects,
    index_repository,
    commit_count,
)
from stats.models import Author


def author_count():
    return Author.objects.count()


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
@pytest.mark.dependency()
def test_register_git_projects(crawler_conf):
    register_git_projects(crawler_conf)

    local_repo = first_repo(is_remote=False)
    assert local_repo is not None

    run_index_local_repository()
    run_index_remote_repository()


def run_index_local_repository():
    repo = first_repo(is_remote=False)
    new_commits = index_repository(repo)
    records_in_db = commit_count(repo)

    # print(f"new_commits = {new_commits}, records_in_db = {records_in_db}")
    assert records_in_db == new_commits
    assert author_count() == 2  # what's the right number?

    # create some test commits and only new commits will be indexed
    create_some_commit(repo.name, "d1.txt")
    create_some_commit(repo.name, "d2.asc")
    assert index_repository(repo) == 2


def run_index_remote_repository():
    index_repository(first_repo(is_remote=True))


def create_some_commit(repo_path: str, file_name: str = "dummy.txt") -> None:
    repo = GitRepository(repo_path).repo
    a_file = f"{repo_path}/{file_name}"
    with open(a_file, "w") as f:
        f.write("something\n")
    repo.index.add(a_file)
    repo.index.commit("some commit")
