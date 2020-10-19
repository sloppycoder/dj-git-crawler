def test_stats_endpoints(client):
    response = client.get("/stats/job")
    assert response.status_code == 401
