---
status: pending
created: 2026-02-02
started: null
completed: null
---
# Task: Injectable init_db

## Description
Update `app/core/db.py:init_db()` to accept an injected engine or session parameter instead of using a global. Ensure all SQLModel tables are registered before table creation.

## Background
The `init_db()` function currently uses a global engine, making it impossible to initialize a test database. Additionally, SQLModel requires all model classes to be imported before `create_all()` is called, or tables won't be created.

## Reference Documentation
**Required:**
- Design: PROMPT.md (Milestone 1: Single DB Entrypoint, item 3-4)

**Note:** Read the design document before beginning implementation.

## Technical Requirements
1. Modify `init_db()` signature to accept optional `engine` parameter
2. If no engine provided, fall back to creating one via the factory (from task-01)
3. Import `app.models` (or equivalent) to ensure all SQLModel tables are registered
4. Ensure `SQLModel.metadata.create_all(engine)` uses the injected engine
5. Return the engine used for caller reference

## Dependencies
- task-01-consolidate-db-creation must be completed first
- Knowledge of all model locations in the codebase

## Implementation Approach
1. Update `init_db()` signature: `def init_db(engine: Engine | None = None) -> Engine`
2. Add model imports at the top of the function (not module level to avoid circular imports):
   ```python
   def init_db(engine: Engine | None = None) -> Engine:
       # Import all models to register them with SQLModel
       import app.models  # noqa: F401

       if engine is None:
           engine = create_db_engine()

       SQLModel.metadata.create_all(engine)
       return engine
   ```
3. Update all callers of `init_db()` to handle the new signature
4. Add tests that pass a custom engine and verify tables are created

## Acceptance Criteria

1. **Injectable Engine Parameter**
   - Given the `init_db()` function
   - When I call it with a custom SQLite in-memory engine
   - Then it creates tables in that engine, not the default database

2. **Models Registered**
   - Given a fresh engine passed to `init_db()`
   - When `init_db()` completes
   - Then all application tables exist in the database (User, Account, Transaction, etc.)

3. **Backward Compatible Default**
   - Given `init_db()` called with no arguments
   - When the function executes
   - Then it uses the default database from settings

4. **Return Value**
   - Given any call to `init_db()`
   - When the function completes
   - Then it returns the engine that was used

5. **Unit Tests**
   - Given a test using SQLite in-memory
   - When I call `init_db(test_engine)`
   - Then I can query the tables and they exist

## Metadata
- **Complexity**: Low
- **Labels**: database, initialization, dependency-injection
- **Required Skills**: Python, SQLModel, SQLAlchemy
