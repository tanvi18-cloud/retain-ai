"""Tests for health check endpoints."""

from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient) -> None:
    """GET /health returns the expected health payload."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "RetainAI API",
        "environment": "development",
        "version": "0.1.0",
    }


def test_api_v1_health_endpoint(client: TestClient) -> None:
    """GET /api/v1/health returns the expected health payload."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "RetainAI API",
        "environment": "development",
        "version": "0.1.0",
    }
