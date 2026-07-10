"""Database session helper for CrewAI tools."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlmodel import Session

from app.core.database import get_engine


@contextmanager
def tool_session() -> Generator[Session, None, None]:
    """Open and close a fresh database session for tool execution."""
    with Session(get_engine()) as session:
        yield session
