---
status: pending
created: 2026-02-02
started: null
completed: null
---
# Task: Consolidate DB Creation

## Description
Merge the duplicate database creation logic from `app/core/db.py` and `app/pkgs/database/provider.py` into a single entrypoint. Make engine creation lazy and injectable rather than happening at import time.

## Background
The current codebase has two places creating database engines, leading to confusion about which is authoritative and making it impossible to inject a test database. Import-time side effects prevent tests from substituting their own engine before the production engine is created.

## Reference Documentation
**Required:**
- Design: PROMPT.md (Milestone 1: Single DB Entrypoint)

**Note:** Read the design document before beginning implementation.

## Technical Requirements
1. Identify all locations where SQLAlchemy/SQLModel engines are created
2. Create a single `create_engine` factory function that accepts configuration parameters
3. Remove import-time engine creation — engine should only be created when explicitly requested
4. Ensure the factory function can accept a custom database URL (for SQLite in tests)
5. Maintain backward compatibility with existing code that imports the engine

## Dependencies
- Understanding of current `app/core/db.py` structure
- Understanding of current `app/pkgs/database/provider.py` structure

## Implementation Approach
1. Audit both `app/core/db.py` and `app/pkgs/database/provider.py` to understand current engine creation
2. Create a new factory function `create_db_engine(url: str | None = None, **kwargs)` that:
   - Uses provided URL or falls back to settings
   - Accepts additional engine configuration (pool size, echo, etc.)
   - Does NOT cache or store the engine globally at import time
3. Update all imports to use the new factory
4. Remove duplicate engine creation code
5. Add unit tests verifying the factory accepts custom URLs

## Acceptance Criteria

1. **Single Engine Factory**
   - Given the application codebase
   - When I search for engine creation (`create_engine`, `create_async_engine`)
   - Then there is exactly one factory function that creates engines

2. **Lazy Engine Creation**
   - Given a fresh Python interpreter
   - When I import `app.core.db` or `app.pkgs.database`
   - Then no database connection is established until explicitly requested

3. **Injectable URL**
   - Given the engine factory function
   - When I call it with a custom `database_url` parameter
   - Then it creates an engine connected to that URL instead of the default

4. **Backward Compatibility**
   - Given existing application code that uses the database
   - When the application starts normally
   - Then all database operations work as before

5. **Unit Tests Pass**
   - Given the new factory function
   - When I run `uv run pytest` on tests for this module
   - Then all tests pass including tests for custom URL injection

## Metadata
- **Complexity**: Medium
- **Labels**: database, refactoring, dependency-injection
- **Required Skills**: Python, SQLAlchemy/SQLModel, FastAPI
