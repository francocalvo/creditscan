---
status: pending
created: 2026-02-02
started: null
completed: null
---
# Task: Refactor Repositories for Session Injection

## Description
Refactor all repository classes to stop calling `get_db_session()` internally. Instead, repositories should receive a session through their constructor or method parameters.

## Background
Currently, repositories call `get_db_session()` internally, which creates a hidden dependency on the global database session. This makes it impossible to inject a test session. The new pattern should be `provide(session: Session) -> Repo` where the session is explicitly passed.

## Reference Documentation
**Required:**
- Design: PROMPT.md (Milestone 2: True Injection, items 5 and 7)

**Note:** Read the design document before beginning implementation.

## Technical Requirements
1. Identify all repository classes in the codebase
2. Remove internal `get_db_session()` calls from each repository
3. Add `session: Session` as a constructor parameter to each repository
4. Store the session as an instance attribute
5. Update all repository methods to use `self.session` instead of calling `get_db_session()`
6. Update repository instantiation sites to pass the session

## Dependencies
- Milestone 1 must be completed (single DB entrypoint exists)
- Understanding of the provider pattern used in the codebase

## Implementation Approach
1. Audit all files in `app/pkgs/*/repositories/` to find repository classes
2. For each repository class:
   ```python
   # Before
   class UserRepository:
       def get_by_id(self, id: int) -> User | None:
           session = get_db_session()
           return session.get(User, id)

   # After
   class UserRepository:
       def __init__(self, session: Session):
           self.session = session

       def get_by_id(self, id: int) -> User | None:
           return self.session.get(User, id)
   ```
3. Update the `provide()` functions to accept and pass the session
4. Temporarily allow both patterns during migration if needed
5. Add unit tests that instantiate repositories with a test session

## Acceptance Criteria

1. **No Internal get_db_session Calls**
   - Given the repository codebase
   - When I search for `get_db_session()` calls inside repository classes
   - Then no matches are found

2. **Constructor Session Injection**
   - Given any repository class
   - When I instantiate it
   - Then it requires a `session` parameter

3. **Session Used for All Operations**
   - Given a repository instantiated with a test session
   - When I call any repository method
   - Then it uses the injected session, not a global one

4. **Provider Pattern Updated**
   - Given the `provide()` function for a repository
   - When I call `provide(session=my_session)`
   - Then it returns a repository bound to `my_session`

5. **Unit Tests**
   - Given a repository with an injected SQLite session
   - When I perform CRUD operations
   - Then they succeed using the test database

## Metadata
- **Complexity**: High
- **Labels**: repositories, dependency-injection, refactoring
- **Required Skills**: Python, SQLModel, repository pattern
