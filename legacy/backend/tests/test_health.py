"""
Health check API tests - Run first to verify backend is up
"""
import pytest
import os

# BASE_URL: Use environment variable if available, otherwise fallback to production URL
# Import BASE_URL from conftest
from tests.conftest import BASE_URL
BASE_URL = BASE_URL.rstrip('/')


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint_returns_200(self, api_client):
        """Test that health endpoint returns 200 OK"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
    
    def test_health_response_structure(self, api_client):
        """Test health response has correct structure"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "database" in data
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
    
    def test_api_docs_endpoint(self, api_client):
        """Test API docs endpoint is accessible"""
        response = api_client.get(f"{BASE_URL}/api/docs")
        # API docs should return 200 (HTML page)
        assert response.status_code == 200
