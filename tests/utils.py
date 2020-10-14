from pydriller import GitRepository

from stats.models import Commit, Repository, Author


def commit_count(repo):
    return Commit.objects.filter(repo=repo).count()


def first_repo(is_remote):
    return Repository.objects.filter(is_remote=is_remote).first()


def author_count():
    return Author.objects.count()


def repository_count():
    return Repository.objects.count()


def create_some_commit(repo_path: str, file_name: str = "dummy.txt") -> None:
    repo = GitRepository(repo_path).repo
    a_file = f"{repo_path}/{file_name}"
    with open(a_file, "w") as f:
        f.write("something\n")
    repo.index.add(a_file)
    repo.index.commit("some commit")
