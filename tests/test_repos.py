import pytest
from repos.models import Author


@pytest.mark.django_db
def test_repos_index(client):
    response = client.get("/repos/")
    assert "authors" in response.json()


@pytest.mark.django_db
def test_create_new_author(client):
    Author(name="test", email="test@test.com").save()
    assert Author.objects.count() == 1
