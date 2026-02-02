---
status: pending
created: 2026-02-02
started: null
completed: null
---
# Task: SQLite In-Memory Fixture

## Description
Create a pytest fixture that provides an SQLite in-memory database engine with proper configuration. Override FastAPI's `get_db` dependency to yield sessions bound to this test engine.

## Background
Tests need to run against an isolated, fast database that doesn't require external services. SQLite in-memory with `StaticPool` allows all connections to share the same in-memory database, and `check_same_thread=False` allows multi-threaded access needed by some test scenarios.

## Reference Documentation
**Required:**
- Design: PROMPT.md (Milestone 4: Rebuild Pytest DB Layer, items 13-15)

**Note:** Read the design document before beginning implementation.

## Technical Requirements
1. Create SQLite in-memory engine with:
   - `StaticPool` to share the connection across threads
   - `check_same_thread=False` for SQLite
   - Proper URL: `sqlite:///:memory:`
2. Create pytest fixtures for engine, session, and test client
3. Override `app.deps.get_db` (or equivalent) in fixtures
4. Call `init_db(engine)` to create tables before tests
5. Implement clean state between tests (transaction rollback preferred)

## Dependencies
- Milestone 1 completed (injectable `init_db`)
- task-01-fix-test-imports completed
- FastAPI TestClient knowledge

## Implementation Approach
1. Create/update `backend/tests/conftest.py`:
   ```python
   import pytest
   from sqlalchemy.pool import StaticPool
   from sqlmodel import Session, create_engine, SQLModel
   from fastapi.testclient import TestClient

   from app.main import app
   from app.deps import get_db
   from app.core.db import init_db

   @pytest.fixture(name="engine", scope="session")
   def engine_fixture():
       engine = create_engine(
           "sqlite:///:memory:",
           connect_args={"check_same_thread": False},
           poolclass=StaticPool,
       )
       init_db(engine)
       return engine

   @pytest.fixture(name="session")
   def session_fixture(engine):
       connection = engine.connect()
       transaction = connection.begin()
       session = Session(bind=connection)

       yield session

       session.close()
       transaction.rollback()
       connection.close()

   @pytest.fixture(name="client")
   def client_fixture(session: Session):
       def get_db_override():
           yield session

       app.dependency_overrides[get_db] = get_db_override
       with TestClient(app) as client:
           yield client
       app.dependency_overrides.clear()
   ```
2. Verify tables are created via `init_db(engine)`
3. Test the fixtures with a simple test
4. Document the fixture usage in a comment or docstring

## Acceptance Criteria

1. **SQLite Engine Created**
   - Given the `engine` fixture
   - When I inspect the engine URL
   - Then it is `sqlite:///:memory:`

2. **StaticPool Configured**
   - Given the `engine` fixture
   - When I check the pool class
   - Then it uses `StaticPool`

3. **Tables Created**
   - Given the `engine` fixture
   - When I inspect the database
   - Then all application tables exist

4. **Session Fixture Works**
   - Given the `session` fixture
   - When I use it in a test to insert and query data
   - Then operations succeed

5. **Transaction Rollback**
   - Given two tests using the `session` fixture
   - When the first test inserts data
   - Then the second test sees a clean database (no data from first test)

6. **Client Fixture Overrides Dependency**
   - Given the `client` fixture
   - When I make an API request
   - Then it uses the test session, not the production database

7. **No Postgres Connection**
   - Given tests running with these fixtures
   - When I check network connections
   - Then no connection to Postgres is made

## Metadata
- **Complexity**: Medium
- **Labels**: testing, fixtures, sqlite, pytest
- **Required Skills**: Python, pytest, SQLAlchemy, FastAPI TestClient
