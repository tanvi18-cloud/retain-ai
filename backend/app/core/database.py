"""SQLModel database engine, session management, and initialization."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.engine import Engine
from sqlalchemy.event import listen
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import Settings, get_settings

_engine: Engine | None = None


def _configure_sqlite_connection(dbapi_connection: object, _connection_record: object) -> None:
    """Enable SQLite foreign key enforcement for relational integrity."""
    cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def configure_engine(database_url: str) -> Engine:
    """Create or replace the global SQLModel engine for the given database URL."""
    global _engine

    if _engine is not None:
        _engine.dispose()

    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    _engine = create_engine(database_url, connect_args=connect_args)

    if database_url.startswith("sqlite"):
        listen(_engine, "connect", _configure_sqlite_connection)

    return _engine


def get_engine(settings: Settings | None = None) -> Engine:
    """Return the configured engine, initializing from settings when needed."""
    global _engine

    if _engine is None:
        resolved_settings = settings or get_settings()
        configure_engine(resolved_settings.database_url)

    return _engine


def reset_engine() -> None:
    """Dispose and clear the global engine (used in tests)."""
    global _engine

    if _engine is not None:
        _engine.dispose()
    _engine = None


def init_db(engine: Engine | None = None) -> None:
    """Create all database tables registered with SQLModel metadata."""
    import app.models  # noqa: F401

    target_engine = engine or get_engine()
    SQLModel.metadata.create_all(target_engine)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session for request-scoped dependency injection."""
    with Session(get_engine()) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
