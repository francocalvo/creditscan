---
status: pending
created: 2026-02-02
started: null
completed: null
---
# Task: Fix Test Imports

## Description
Fix the import structure in `backend/tests/` to resolve `ModuleNotFoundError`. Tests currently try to import `app.tests...` but tests live under `backend/tests`, not inside the `app` package.

## Background
The test configuration in `conftest.py` has incorrect imports that cause `ModuleNotFoundError` when running pytest. Tests should use relative imports within the `backend/tests` directory or absolute imports from `backend.tests`.

## Reference Documentation
**Required:**
- Design: PROMPT.md (Milestone 4: Rebuild Pytest DB Layer, item 12)

**Note:** Read the design document before beginning implementation.

## Technical Requirements
1. Audit `backend/tests/conftest.py` for incorrect imports
2. Identify the correct import path structure based on project layout
3. Fix imports to use either:
   - Relative imports: `from .utils.user import create_test_user`
   - Or correct absolute imports based on PYTHONPATH
4. Ensure `__init__.py` files exist where needed
5. Verify pytest can discover and import all test files

## Dependencies
- Understanding of the project's Python path configuration
- Knowledge of pytest's import system

## Implementation Approach
1. Check the project structure:
   ```
   backend/
   ├── app/
   │   └── ...
   └── tests/
       ├── __init__.py
       ├── conftest.py
       └── utils/
           ├── __init__.py
           └── user.py
   ```
2. Update `conftest.py` imports:
   ```python
   # Before (WRONG)
   from app.tests.utils.user import create_test_user

   # After (CORRECT - relative)
   from .utils.user import create_test_user

   # Or (CORRECT - absolute if backend is in PYTHONPATH)
   from backend.tests.utils.user import create_test_user
   ```
3. Add missing `__init__.py` files if needed
4. Update `pyproject.toml` or `pytest.ini` if pythonpath needs configuration
5. Run `uv run pytest --collect-only` to verify all tests are discovered

## Acceptance Criteria

1. **No Import Errors**
   - Given the test directory
   - When I run `uv run pytest --collect-only`
   - Then no `ModuleNotFoundError` or `ImportError` occurs

2. **Correct Import Style**
   - Given `backend/tests/conftest.py`
   - When I inspect the imports
   - Then they use valid relative or absolute import paths

3. **Init Files Present**
   - Given the `backend/tests/` directory tree
   - When I check for `__init__.py` files
   - Then they exist in `tests/` and all subdirectories containing Python files

4. **Tests Discoverable**
   - Given the pytest configuration
   - When I run `uv run pytest --collect-only`
   - Then all test files and functions are listed

5. **Sample Test Runs**
   - Given a simple test file
   - When I run `uv run pytest backend/tests/test_sample.py -v`
   - Then the test executes without import errors

## Metadata
- **Complexity**: Low
- **Labels**: testing, imports, configuration
- **Required Skills**: Python, pytest, module system
