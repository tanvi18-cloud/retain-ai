"""Shared fixtures for agent and LLM tests."""

import pytest
from sqlmodel import Session, SQLModel

from app.core.config import Settings
from app.core.database import configure_engine, init_db, reset_engine
from app.core.llm import reset_llm_status_cache
from app.seed.seed_database import seed_database


@pytest.fixture
def agent_settings(test_settings: Settings) -> Settings:
    """Settings with mock LLM mode enabled for deterministic agent tests."""
    reset_llm_status_cache()
    return test_settings.model_copy(update={"mock_llm_mode": True})


@pytest.fixture
def agent_seeded_engine(test_settings: Settings):
    """Provide a seeded SQLite engine for agent and tool tests."""
    reset_engine()
    reset_llm_status_cache()
    engine = configure_engine(test_settings.database_url)
    SQLModel.metadata.drop_all(engine)
    init_db(engine)
    with Session(engine) as session:
        seed_database(session, skip_if_complete=False)
    yield engine
    SQLModel.metadata.drop_all(engine)
    reset_engine()
    reset_llm_status_cache()


@pytest.fixture
def agent_seeded_session(agent_seeded_engine):
    """Provide a session bound to the agent seeded test engine."""
    with Session(agent_seeded_engine) as session:
        yield session
