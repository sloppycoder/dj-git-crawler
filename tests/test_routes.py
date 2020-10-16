def test_stats_endpoints(client):
    response = client.get("/stats/scan")
    assert response.status_code == 401

    response = client.get("/stats/discover")
    assert response.status_code == 401

    response = client.get("/stats/stat")
    assert response.status_code == 401
