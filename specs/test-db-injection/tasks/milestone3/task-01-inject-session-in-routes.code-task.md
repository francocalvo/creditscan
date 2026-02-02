---
status: pending
created: 2026-02-02
started: null
completed: null
---
# Task: Inject Session in API Routes

## Description
Update all API routes that use `provide()` with hidden database access to explicitly accept a `session: SessionDep` parameter and pass it to the provider functions.

## Background
Many routes currently call `usecase = provide()` which internally creates or retrieves a cached session. This hides the database dependency and makes it impossible to inject a test session via FastAPI's dependency override system. Routes must explicitly declare their session dependency.

## Reference Documentation
**Required:**
- Design: PROMPT.md (Milestone 3: Make API Routes Consume SessionDep, item 9)

**Note:** Read the design document before beginning implementation.

## Technical Requirements
1. Define `SessionDep` as a FastAPI dependency type alias if not already defined
2. Identify all routes that call `provide()` or similar functions with hidden DB access
3. Add `session: SessionDep` parameter to each route function
4. Update `provide()` calls to pass the session: `provide(session)`
5. Ensure the session is properly typed for IDE support

## Dependencies
- Milestone 2 must be completed (providers accept session parameter)
- Understanding of FastAPI dependency injection

## Implementation Approach
1. Create or verify `SessionDep` type alias:
   ```python
   from typing import Annotated
   from fastapi import Depends
   from sqlmodel import Session

   def get_db() -> Generator[Session, None, None]:
       # This will be overridden in tests
       with Session(engine) as session:
           yield session

   SessionDep = Annotated[Session, Depends(get_db)]
   ```
2. For each route file in `app/api/routes/`:
   ```python
   # Before
   @router.get("/users/{id}")
   def get_user(id: int) -> UserPublic:
       usecase = provide_get_user_usecase()
       return usecase.execute(id)

   # After
   @router.get("/users/{id}")
   def get_user(id: int, session: SessionDep) -> UserPublic:
       usecase = provide_get_user_usecase(session)
       return usecase.execute(id)
   ```
3. Update all routes systematically, file by file
4. Run the application to verify routes still work
5. Add integration tests that override `get_db` dependency

## Acceptance Criteria

1. **SessionDep Defined**
   - Given the application dependencies module
   - When I import `SessionDep`
   - Then it is a properly typed FastAPI dependency

2. **All Routes Declare Session**
   - Given routes that perform database operations
   - When I inspect their function signatures
   - Then they have a `session: SessionDep` parameter

3. **Session Passed to Providers**
   - Given a route with `session: SessionDep`
   - When the route calls a provider function
   - Then it passes `session` as an argument

4. **Dependency Override Works**
   - Given a test that overrides `get_db` with a test session generator
   - When I call the route via TestClient
   - Then the route uses the test session

5. **Application Functions Normally**
   - Given the updated application
   - When I run it and call various endpoints
   - Then all endpoints work as before

## Metadata
- **Complexity**: Medium
- **Labels**: api, routes, dependency-injection, fastapi
- **Required Skills**: Python, FastAPI, dependency injection
