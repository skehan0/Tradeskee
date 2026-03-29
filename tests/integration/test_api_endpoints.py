"""
Integration tests for main API endpoints.

These test the actual HTTP endpoints using FastAPI's TestClient.
We're testing the whole request/response cycle without running a server.

Learning concepts:
- TestClient for API testing
- HTTP status codes
- JSON response validation
- Using fixtures from conftest.py
"""
import pytest
from fastapi import status


class TestRootEndpoint:
    """Tests for the root '/' endpoint."""
    
    def test_root_returns_200(self, test_client):
        """Test root endpoint returns 200 OK status."""
        response = test_client.get("/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_root_returns_welcome_message(self, test_client):
        """Test root endpoint returns welcome message."""
        response = test_client.get("/")
        data = response.json()
        
        assert "message" in data
        assert data["message"] == "Welcome to Tradeskee API"
    
    def test_root_returns_version(self, test_client):
        """Test root endpoint includes version."""
        response = test_client.get("/")
        data = response.json()
        
        assert "version" in data
        assert data["version"] == "2.0.0"
    
    def test_root_includes_docs_link(self, test_client):
        """Test root endpoint includes link to documentation."""
        response = test_client.get("/")
        data = response.json()
        
        assert "docs" in data
        assert "/api/v1/docs" in data["docs"]
    
    def test_root_includes_health_link(self, test_client):
        """Test root endpoint includes health check link."""
        response = test_client.get("/")
        data = response.json()
        
        assert "health" in data
        assert "/health" in data["health"]


class TestHealthCheckEndpoint:
    """Tests for the /health endpoint."""
    
    def test_health_check_returns_200(self, test_client):
        """Test health check returns 200 OK."""
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
    
    def test_health_check_status_is_healthy(self, test_client):
        """Test health check reports healthy status."""
        response = test_client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
    
    def test_health_check_includes_app_info(self, test_client):
        """Test health check includes application information."""
        response = test_client.get("/health")
        data = response.json()
        
        assert "app" in data
        assert "version" in data
        assert "environment" in data
        
        assert data["app"] == "Tradeskee"
        assert data["version"] == "2.0.0"
    
    def test_health_check_returns_json(self, test_client):
        """Test health check returns JSON content type."""
        response = test_client.get("/health")
        assert response.headers["content-type"] == "application/json"


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""
    
    def test_openapi_json_endpoint(self, test_client):
        """Test OpenAPI JSON schema is accessible."""
        response = test_client.get("/api/v1/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Tradeskee"
    
    def test_swagger_docs_endpoint(self, test_client):
        """Test Swagger UI is accessible."""
        response = test_client.get("/api/v1/docs")
        assert response.status_code == status.HTTP_200_OK


class TestNonExistentEndpoints:
    """Test error handling for non-existent endpoints."""
    
    def test_nonexistent_endpoint_returns_404(self, test_client):
        """Test accessing non-existent endpoint returns 404."""
        response = test_client.get("/this/does/not/exist")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_wrong_api_version_returns_404(self, test_client):
        """Test wrong API version in URL returns 404."""
        response = test_client.get("/api/v2/stocks/quote")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# 🎓 LEARNING EXERCISE: Testing with different HTTP methods

class TestHTTPMethods:
    """Test different HTTP methods on endpoints."""
    
    def test_health_only_accepts_get(self, test_client):
        """Test health endpoint only accepts GET requests."""
        # GET should work
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        # POST should fail
        response = test_client.post("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # PUT should fail
        response = test_client.put("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_root_only_accepts_get(self, test_client):
        """Test root endpoint only accepts GET requests."""
        # GET should work
        response = test_client.get("/")
        assert response.status_code == status.HTTP_200_OK
        
        # POST should fail
        response = test_client.post("/")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
