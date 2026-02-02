"""Database provider implementation.

This module provides the single source of truth for database engine creation.
The engine is created lazily and can be overridden for testing.
"""

from collections.abc import Generator
from typing import TYPE_CHECKING

from sqlmodel import Session, create_engine

if TYPE_CHECKING:
    from sqlalchemy import Engine

# Private engine instance - lazily initialized
_engine: "Engine | None" = None


def get_engine() -> "Engine":
    """Get the database engine, creating it lazily if needed.

    Returns:
        Engine: The SQLAlchemy/SQLModel engine.
    """
    global _engine
    if _engine is None:
        from app.core.config import settings

        database_url = settings.SQLALCHEMY_DATABASE_URI
        _engine = create_engine(database_url.unicode_string(), pool_pre_ping=True)
    return _engine


def set_engine(engine: "Engine | None") -> None:
    """Set the database engine (for testing).

    Args:
        engine: The engine to use, or None to reset to lazy initialization.
    """
    global _engine
    _engine = engine


def get_db() -> Generator[Session, None, None]:
    """Get a database session as a generator (for FastAPI Depends).

    Yields:
        Session: A SQLModel session.
    """
    with Session(get_engine()) as session:
        yield session


def get_db_session() -> Session:
    """Get a database session directly (not as a generator).

    Returns:
        Session: A SQLModel session.
    """
    return Session(get_engine())
