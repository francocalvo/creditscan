# Plan: Fix Remaining 5 Failing Tests

## Overview

This plan addresses the 5 remaining failing tests to complete M4:

1. `tests/scripts/test_backend_pre_start.py::test_init_successful_connection`
2. `tests/scripts/test_test_pre_start.py::test_init_successful_connection`
3. `tests/api/routes/test_login.py::test_reset_password`
4. `tests/api/routes/test_users.py::test_get_existing_user_permissions_error`
5. `tests/api/routes/test_users.py::test_retrieve_users`

## Task 1: Fix Mock Assertion in Pre-Start Tests (2 files)

### Problem
Both `test_backend_pre_start.py` and `test_test_pre_start.py` use `called_once_with` on line 31, which is NOT a valid Mock assertion method. It's a property that always returns a truthy MagicMock, so the assertion always passes even when incorrect.

### Location
- `backend/tests/scripts/test_backend_pre_start.py:31`
- `backend/tests/scripts/test_test_pre_start.py:31`

### Current Code
```python
assert session_mock.exec.called_once_with(select(1)), (
    "The session should execute a select statement once."
)
```

### Fix
Change to the correct assertion method `assert_called_once_with`:
```python
session_mock.exec.assert_called_once_with(select(1))
```

Note: Remove the `assert` wrapper since `assert_called_once_with` raises `AssertionError` on failure.

## Task 2: Fix reset_password API Route (M3 Scope)

### Problem
The `reset_password` route in `login.py:104` tries to set `user.hashed_password` on the result of `UserService.get_user_by_email()`, which returns a `UserPublic` Pydantic model. Pydantic models don't allow attribute assignment by default, and even if they did, the change wouldn't persist to the database.

### Location
`backend/app/api/routes/login.py:84-107`

### Current Code (lines 93-106)
```python
auth_user_service = provide_user_service(session)
user = auth_user_service.get_user_by_email(email)

if not user:
    raise HTTPException(...)
elif not user.is_active:
    raise HTTPException(status_code=400, detail="Inactive user")
hashed_password = get_password_hash(password=body.new_password)
user.hashed_password = hashed_password  # ← FAILS: UserPublic has no hashed_password
session.add(user)
session.commit()
```

### Fix
Use `UserRepository` directly to get the ORM `User` model, then update:

1. Add import: `from app.domains.users.repository import provide as provide_repository`
2. Replace the service call with repository call to get ORM model
3. Update the ORM model and commit

New code structure:
```python
user_repo = provide_repository(session)
user = user_repo.get_by_email(email)

if not user:
    raise HTTPException(...)
elif not user.is_active:
    raise HTTPException(status_code=400, detail="Inactive user")
hashed_password = get_password_hash(password=body.new_password)
user.hashed_password = hashed_password
session.add(user)
session.commit()
```

## Task 3: Fix test_get_existing_user_permissions_error Test

### Problem
The test passes a random UUID that doesn't exist in the database. The API route (`get_user.py`) checks if the user exists first, and if not, returns 404 before ever checking permissions. The test expects 403.

### Location
`backend/tests/api/routes/test_users.py:106-114`

### Current Test
```python
def test_get_existing_user_permissions_error(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",  # Random non-existent user
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
```

### Fix
The test needs to query an EXISTING user that the normal user doesn't have permission to view. Options:

**Option A (Recommended)**: Create a different user in the test and try to access them
- Add `db: Session` parameter to the test
- Create a new user using `UserRepository(db).create()`
- Try to access that user with normal_user_token_headers
- Expect 403

**Option B**: Access the superuser's record
- Get the superuser ID from the database
- Try to access it with normal_user_token_headers
- Expect 403

Going with Option A for test isolation.

## Task 4: Add list_users Route for test_retrieve_users

### Problem
The test expects `GET /users/` to return a paginated list of users, but no such route exists. The users routes module only includes CRUD operations for individual users.

### Location
- Missing route: `backend/app/api/routes/users/list_users.py` (needs creation)
- Route registration: `backend/app/api/routes/users/__init__.py`

### Test Expectation (from test_users.py:150-169)
```python
r = client.get(f"{settings.API_V1_STR}/users/", headers=superuser_token_headers)
all_users = r.json()
assert len(all_users["data"]) > 1
assert "count" in all_users
```

### Fix
Create a new route file `list_users.py` that:
1. Requires superuser privileges (consistent with other admin operations)
2. Uses the existing `SearchUsersUseCase` from `app.domains.users.usecases.search_users`
3. Returns `UsersPublic` model with `data` and `count` fields
4. Supports optional query parameters for filtering/pagination

Route structure:
```python
@router.get("/", response_model=UsersPublic)
def list_users(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all users (superusers only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, ...)
    usecase = provide_search_users(session)
    return usecase.execute(skip=skip, limit=limit)
```

Then register it in `__init__.py`.

## Implementation Order

1. **Task 1** (simplest): Fix mock assertions in both pre_start test files
2. **Task 2** (API fix): Fix reset_password to use UserRepository
3. **Task 3** (test fix): Update test_get_existing_user_permissions_error
4. **Task 4** (new route): Create list_users route

## Verification

After all fixes:
1. `uv run pytest backend/tests/` - all tests should pass
2. `uv run ruff check backend/` - no linting errors
3. `uv run pyright backend/` - no type errors (if applicable)

## Success Criteria

- [ ] All 5 failing tests now pass
- [ ] No new test failures introduced
- [ ] ruff check passes
- [ ] Code follows existing patterns in the codebase
