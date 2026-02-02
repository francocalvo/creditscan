# Improve Test Suite with Database Injection

## Objective

Refactor the backend test infrastructure to use an injected SQLite in-memory database, eliminating the Postgres dependency and removing all hidden global DB/session usage.

## Context

The current test suite has several blockers:
- `backend/tests/conftest.py` imports `app.tests...` but tests live under `backend/tests` → `ModuleNotFoundError`
- Tests reference `app.crud` + outdated fields (e.g., `UserCreate(disabled=...)`), but `app/crud.py` doesn't exist and `UserCreate` has no `disabled` field
- Many routes use `provide()` which creates/caches its own Session (`@lru_cache` + `get_db_session()`), so overriding FastAPI `get_db` won't affect most endpoints

## Requirements

### Milestone 1: Single DB Entrypoint

1. Consolidate DB creation (avoid both `app/core/db.py` and `app/pkgs/database/provider.py` each creating an engine)
2. Make engine creation lazy + injectable (factory function), not import-time side effects
3. Update `app/core/db.py:init_db()` to accept injected `engine` or `session`
4. Ensure `app.models` is imported so all SQLModel tables are registered

### Milestone 2: True Injection (Remove Session Singletons)

5. Repositories: stop calling `get_db_session()` internally
6. Remove `@lru_cache` from any provider that captures a Session
7. New pattern: `provide(session: Session) -> Repo`
8. Services/usecases: thread `session` through providers so each request/test builds a usecase graph bound to the injected session

### Milestone 3: Make API Routes Consume SessionDep

9. For each route doing `usecase = provide()` with hidden DB:
   - Add `session: SessionDep` parameter
   - Call `provide(session)` or inject via `Depends(...)`
10. Fix mixed "public model vs ORM" usage (e.g., `app/api/routes/login.py:reset_password` mutates a `UserPublic`)
11. Standardize: use repository for ORM mutation, service/usecase for public output

### Milestone 4: Rebuild Pytest DB Layer (SQLite)

12. Fix test imports: use relative imports inside `backend/tests` (e.g., `from .utils.user import ...`)
13. Add SQLite in-memory engine fixture with `StaticPool` + `check_same_thread=False`
14. Override FastAPI `get_db` dependency to yield sessions bound to the test engine
15. Ensure clean state between tests (transaction rollback or table truncation)
16. Update tests to match current domains/models:
    - Replace `app.crud.*` with domain services/usecases or direct SQLModel session queries
    - Rename/remove outdated fields (`disabled` → `is_active`, etc.)

## Constraints

- No patching or mocking of internal DB mechanisms
- DB must be passed explicitly through params/deps
- No cached providers may hold a Session across requests/tests
- Must maintain existing API behavior

## Success Criteria

- [ ] `uv run pytest` passes with all tests
- [ ] `ruff check .` passes with no errors
- [ ] `uv run pyright` passes (if app types change)
- [ ] All tests run using only SQLite in-memory database
- [ ] No global engine/session mutation exists
- [ ] No mocked internal DB; DB injected via params/deps
- [ ] No cached providers hold a Session across requests/tests

## Progress Log

- [ ] Milestone 1: Single DB entrypoint complete
- [ ] Milestone 2: Session singletons removed
- [ ] Milestone 3: API routes use SessionDep
- [ ] Milestone 4: Pytest DB layer rebuilt

## Notes

- Prefer Option A (per-test transaction + rollback) for clean state if feasible
- When updating tests, check for any other outdated field references beyond `disabled`
- The `provide()` pattern with `@lru_cache` is the main source of hidden state

LOOP_COMPLETE
