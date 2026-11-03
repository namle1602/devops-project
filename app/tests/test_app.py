
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


def test_dashboard_sections(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Release Overview" in response.data
    assert b"Current Release Details" in response.data
    assert b"Release History" in response.data
    assert b"Release Info API" in response.data


def test_releases_empty(client, monkeypatch, tmp_path):
    missing = tmp_path / "missing.json"
    monkeypatch.setenv("RELEASE_HISTORY_FILE", str(missing))

    response = client.get("/api/releases")

    assert response.status_code == 200
    assert response.get_json() == {"releases": []}


def test_releases_with_data(client, monkeypatch, tmp_path):
    import json

    history_file = tmp_path / "releases.json"
    history = {
        "schema_version": 1,
        "releases": [
            {
                "version": "32",
                "commit": "869301038286ac0dbee106391aa32d8d07c1dacf",
                "image": "ghcr.io/namle1602/devops-flask-app:32",
                "environment": "production",
                "status": "success",
                "deployed_at": None,
                "cd_build": 24
            }
        ]
    }

    history_file.write_text(
        json.dumps(history), encoding="utf-8"
    )
    monkeypatch.setenv("RELEASE_HISTORY_FILE", str(history_file))

    response = client.get("/api/releases")

    assert response.status_code == 200
    data = response.get_json()
    assert len(data["releases"]) == 1
    assert data["releases"][0]["version"] == "32"


def test_releases_invalid_json(client, monkeypatch, tmp_path):
    history_file = tmp_path / "releases.json"
    history_file.write_text("{invalid json", encoding="utf-8")
    monkeypatch.setenv("RELEASE_HISTORY_FILE", str(history_file))

    response = client.get("/api/releases")

    assert response.status_code == 503
    assert response.get_json()["error"] == "Release history unavailable"
