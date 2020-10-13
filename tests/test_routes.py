import pytest


@pytest.mark.django_db
def test_stats_index(client):
    response = client.get("/stats/")
    assert "authors" in response.json()
