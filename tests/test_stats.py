import pytest
from stats.models import Author


@pytest.mark.django_db
def test_stats_index(client):
    response = client.get("/stats/")
    assert "authors" in response.json()


@pytest.mark.django_db
def test_create_new_author(client):
    Author(name="test", email="test@test.com").save()
    assert Author.objects.count() == 1
