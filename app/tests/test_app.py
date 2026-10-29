
import os
import sys
import pytest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"DevOps Release Tracker" in response.data
    assert b"Version" in response.data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}


def test_info_endpoint(client):
    response = client.get("/api/info")
    assert response.status_code == 200

    data = response.get_json()
    assert data["application"] == "devops-release-tracker"
    assert "version" in data
    assert "environment" in data
    assert "commit" in data


def test_message_endpoint(client):
    response = client.get("/api/message")
    assert response.status_code == 200

    data = response.get_json()
    assert "version" in data
    assert data["message"] == "Welcome to DevOps Release Tracker!"
