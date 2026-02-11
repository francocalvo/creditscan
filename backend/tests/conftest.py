import uuid as uuid_module
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.sqltypes import Uuid
from sqlmodel import Session, create_engine

from app.core.config import settings
from app.core.db import init_db
from app.main import app
from app.pkgs.database import get_db, set_engine

from .utils.user import authentication_token_from_email
from .utils.utils import get_superuser_token_headers

settings.USERS_OPEN_REGISTRATION = True


# Enable SQLite foreign key support for referential integrity
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record):
    """Enable foreign key support for SQLite connections."""
    if "sqlite" in str(type(dbapi_connection)):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Monkey-patch the Uuid type's bind processor to handle string UUIDs
# This is needed for SQLite compatibility since SQLite stores UUIDs as strings
_original_bind_processor = Uuid.bind_processor


def _patched_bind_processor(self, dialect):
    """Return a bind processor that handles both UUID objects and strings."""
    if dialect.supports_native_uuid:
        # Native UUID support - still need to handle string inputs
        def process(value):
            if value is not None:
                if isinstance(value, str):
                    return uuid_module.UUID(value)
            return value

        return process
    else:
        # Non-native UUID - store as string
        def process(value):
            if value is not None:
                if isinstance(value, str):
                    value = uuid_module.UUID(value)
                return (
                    value.hex
                    if hasattr(self, "as_uuid") and self.as_uuid
                    else str(value)
                )
            return value

        return process


# Apply the patch before any tests run
Uuid.bind_processor = _patched_bind_processor  # type: ignore


@pytest.fixture(scope="session")
def engine() -> Generator:
    """Create a SQLite in-memory engine for testing.

    Uses StaticPool to ensure the same connection is reused across the session,
    and check_same_thread=False to allow SQLite to be used across threads.
    """
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Set the test engine globally so all code uses it
    set_engine(test_engine)

    # Create tables and seed superuser
    init_db(test_engine)

    yield test_engine

    # Reset the engine after tests complete
    set_engine(None)


@pytest.fixture(scope="function")
def db(engine) -> Generator[Session, None, None]:
    """Provide a database session with per-test transaction rollback.

    Each test gets a fresh session. Changes are rolled back after the test
    to ensure test isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI test client with dependency override for get_db.

    The get_db dependency is overridden to return the test session,
    ensuring all API calls use the same transactional session as the test.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="function")
def normal_user_token_headers(
    client: TestClient,  # noqa: ARG001
    db: Session,  # noqa: ARG001
) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
