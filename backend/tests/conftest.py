"""Shared pytest fixtures."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.database import configure_engine, get_engine, init_db, reset_engine
from app.main import create_app
from app.seed.seed_database import seed_database

pytest_plugins = ["tests.conftest_repositories"]


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Return deterministic settings for tests."""
    database_path = tmp_path / "test_api.db"
    return Settings(
        app_name="RetainAI",
        app_env="development",
        debug=False,
        frontend_origin="http://localhost:5173",
        database_url=f"sqlite:///{database_path.as_posix()}",
    )


@pytest.fixture
def seeded_client(test_settings: Settings) -> TestClient:
    """Return a test client backed by the full synthetic seed dataset."""
    reset_engine()
    configure_engine(test_settings.database_url)
    init_db()
    with Session(get_engine()) as session:
        seed_database(session, skip_if_complete=False)

    application = create_app(settings=test_settings)
    application.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(application) as test_client:
        yield test_client
    reset_engine()


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    """Return a test client with an empty database."""
    reset_engine()
    application = create_app(settings=test_settings)
    application.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(application) as test_client:
        yield test_client
    reset_engine()
