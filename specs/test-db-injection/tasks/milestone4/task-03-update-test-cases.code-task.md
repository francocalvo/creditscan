---
status: pending
created: 2026-02-02
started: null
completed: null
---
# Task: Update Test Cases

## Description
Update all existing test cases to work with the new fixtures and current domain models. Replace references to `app.crud.*` with domain services/usecases or direct SQLModel session queries. Fix outdated field names like `disabled` → `is_active`.

## Background
The existing tests reference outdated code (`app.crud` module that no longer exists) and use field names that have been renamed in the current models. Tests need to be updated to match the current application structure and use the new session injection fixtures.

## Reference Documentation
**Required:**
- Design: PROMPT.md (Milestone 4: Rebuild Pytest DB Layer, item 16)

**Note:** Read the design document before beginning implementation.

## Technical Requirements
1. Replace all `app.crud.*` imports with:
   - Domain services/usecases via providers, OR
   - Direct SQLModel session queries for simple cases
2. Update model field references:
   - `disabled` → `is_active` (inverted logic!)
   - Check for other renamed/removed fields
3. Update test data creation to use current model schemas:
   - `UserCreate` no longer has `disabled` field
   - Check all `*Create` schemas for accuracy
4. Ensure all tests use the `session` or `client` fixture
5. Remove any tests that are no longer relevant

## Dependencies
- task-01-fix-test-imports completed
- task-02-sqlite-inmemory-fixture completed
- Knowledge of current model schemas

## Implementation Approach
1. Inventory all test files and their imports
2. For each test file:
   ```python
   # Before
   from app.crud import user as user_crud

   def test_create_user(db: Session):
       user_in = UserCreate(email="test@test.com", password="test", disabled=False)
       user = user_crud.create(db, obj_in=user_in)
       assert user.disabled == False

   # After
   from app.pkgs.users.services import UserService
   # or direct session usage

   def test_create_user(session: Session):
       user_in = UserCreate(email="test@test.com", password="test")
       # Option A: Use service
       user_service = provide_user_service(session)
       user = user_service.create(user_in)
       # Option B: Direct session
       user = User(**user_in.model_dump(), hashed_password=hash("test"))
       session.add(user)
       session.commit()

       assert user.is_active == True  # Note: inverted from disabled
   ```
3. Run tests incrementally, fixing failures as they arise
4. Add new tests for any untested critical paths discovered
5. Ensure `uv run pytest` passes with all tests

## Acceptance Criteria

1. **No app.crud Imports**
   - Given the test codebase
   - When I search for `from app.crud` or `import app.crud`
   - Then no matches are found

2. **No Outdated Fields**
   - Given all test files
   - When I search for `disabled` field usage
   - Then no matches are found (replaced with `is_active`)

3. **Current Schemas Used**
   - Given test data creation
   - When I inspect `UserCreate`, `AccountCreate`, etc. usage
   - Then only current schema fields are used

4. **Fixtures Used**
   - Given all test functions
   - When I check their parameters
   - Then they use `session`, `client`, or other fixtures (not raw db)

5. **All Tests Pass**
   - Given the complete test suite
   - When I run `uv run pytest`
   - Then all tests pass

6. **No Postgres Required**
   - Given a fresh environment without Postgres running
   - When I run `uv run pytest`
   - Then all tests pass using SQLite in-memory

## Metadata
- **Complexity**: High
- **Labels**: testing, migrations, models, refactoring
- **Required Skills**: Python, pytest, SQLModel, domain knowledge
