import pytest
from django.test import TestCase


@pytest.mark.django_db
def test_repos_index(client):
    response = client.get("/repos/")
    assert "authors" in response.json()
