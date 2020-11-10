import pytest


@pytest.mark.django_db
def test_stats_endpoints(client):
    response = client.get("/stats/repo?code=s3cr3t")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
