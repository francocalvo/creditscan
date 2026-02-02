# Test Suite DB Injection Refactor

## Objective

Refactor the backend test infrastructure to use an injected SQLite in-memory database, eliminating the Postgres dependency and removing all hidden global DB/session usage.

## Specs Directory

All task files are in: `specs/test-db-injection/tasks/`

## Execution Order

Execute milestones sequentially. Tasks within each milestone can be done in order listed.

### Phase 1: Foundation (Milestone 1)
1. `milestone1/task-01-consolidate-db-creation.code-task.md`
2. `milestone1/task-02-injectable-init-db.code-task.md`

### Phase 2: Dependency Injection (Milestone 2)
3. `milestone2/task-01-refactor-repositories.code-task.md`
4. `milestone2/task-02-remove-lru-cache-sessions.code-task.md`

### Phase 3: API Layer (Milestone 3)
5. `milestone3/task-01-inject-session-in-routes.code-task.md`
6. `milestone3/task-02-fix-model-mutations.code-task.md`

### Phase 4: Test Infrastructure (Milestone 4)
7. `milestone4/task-01-fix-test-imports.code-task.md`
8. `milestone4/task-02-sqlite-inmemory-fixture.code-task.md`
9. `milestone4/task-03-update-test-cases.code-task.md`

## Acceptance Criteria

After all tasks complete, verify:

- [ ] `uv run pytest` passes with all tests
- [ ] `ruff check .` passes with no errors
- [ ] `uv run pyright` passes (if types changed)
- [ ] All tests run using only SQLite in-memory database
- [ ] No global engine/session mutation exists
- [ ] No mocked internal DB; DB injected via params/deps
- [ ] No cached providers hold a Session across requests/tests

## Constraints

- No patching or mocking of internal DB mechanisms
- DB must be passed explicitly through params/deps
- Must maintain existing API behavior
- Prefer transaction rollback for test isolation

## Reference

Main design document: `/Users/francocalvo/personal/facultad/pf/app/PROMPT.md`
