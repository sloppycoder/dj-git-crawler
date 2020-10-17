def test_stats_endpoints(client):
    response = client.get("/stats/scan")
    assert response.status_code == 401
