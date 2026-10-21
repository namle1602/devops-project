import os
import sys
import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_index_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.get_json()

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}

def test_simulate_ci_failure(client):
    response = client.get("/health")

    # Gia lap mot yeu cau sai de kiem tra CI
    assert response.get_json() == {"status": "unhealthy"}