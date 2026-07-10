"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Return deterministic settings for tests."""
    return Settings(
        app_name="RetainAI",
        app_env="development",
        debug=False,
        frontend_origin="http://localhost:5173",
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    """Return a test client with overridden settings."""
    application = create_app(settings=test_settings)
    application.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(application) as test_client:
        yield test_client
