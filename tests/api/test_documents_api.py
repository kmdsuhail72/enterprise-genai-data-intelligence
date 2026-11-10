"""Tests for documents API endpoints."""

import io
from fastapi.testclient import TestClient
from enterprise_ai.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test public health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_health_endpoint():
    """Test versioned health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_admin_config_endpoint():
    """Test admin configuration endpoint."""
    response = client.get("/api/v1/admin/config")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "app_name" in data["data"]

