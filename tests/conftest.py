"""
Shared pytest fixtures and configuration.

Fixtures defined here are available to all tests without importing.
This is pytest's "magic" - it auto-discovers conftest.py files.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def test_client():
    """
    FastAPI test client fixture.
    
    Usage in tests:
        def test_something(test_client):
            response = test_client.get("/health")
            assert response.status_code == 200
    """
    return TestClient(app)


@pytest.fixture
def sample_stock_symbol():
    """
    Sample stock symbol for testing.
    
    Using a fixture instead of hardcoding "AAPL" everywhere
    means we can change it in one place if needed.
    """
    return "AAPL"


@pytest.fixture
def mock_alpha_vantage_quote_response():
    """
    Mock response from Alpha Vantage quote endpoint.
    
    This is what the REAL API returns - we use this to test
    without calling the actual API (saves money, faster, reliable).
    """
    return {
        "Global Quote": {
            "01. symbol": "AAPL",
            "02. open": "150.0000",
            "03. high": "152.5000",
            "04. low": "149.0000",
            "05. price": "151.2500",
            "06. volume": "75000000",
            "07. latest trading day": "2024-02-23",
            "08. previous close": "150.5000",
            "09. change": "0.7500",
            "10. change percent": "0.4987%"
        }
    }


@pytest.fixture
def mock_alpha_vantage_error_response():
    """
    Mock error response from Alpha Vantage.
    
    Used to test how your code handles API errors.
    """
    return {
        "Error Message": "Invalid API call. Please retry or visit the documentation."
    }
