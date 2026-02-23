from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root_endpoint():
    """
    Test the root endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Tradeskee API"
    assert data["version"] == "2.0.0"
    assert data["environment"] == "development"
    assert "docs" in data
    assert "health" in data

def test_health_check():
    """
    Test the health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Tradeskee"
    assert data["version"] == "2.0.0"
    assert data["environment"] == "development"
