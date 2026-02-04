# Testing

This document describes how to run tests for the backend and frontend.

## Backend Tests

The backend uses [pytest](https://docs.pytest.org/) for testing with coverage
support via [coverage.py](https://coverage.readthedocs.io/).

### Running Tests Locally

```bash
cd backend
uv run pytest
```

### Running Tests with Coverage

```bash
cd backend
uv run pytest --cov=app --cov-report=html --cov-report=term-missing --verbose
```

### Running Specific Tests

```bash
cd backend
uv run pytest tests/api/test_endpoints.py
```

### Test Configuration

- Test configuration is in `backend/tests/conftest.py`
- Tests use an in-memory SQLite database for isolation
- Each test runs in its own transaction that is rolled back after completion

## Frontend Tests

The frontend uses [Vitest](https://vitest.dev/) for testing with Vue component
support via [@vue/test-utils](https://test-utils.vuejs.org/).

### Running Tests Locally

```bash
cd frontend
npm run test
```

### Running Tests in Watch Mode

```bash
cd frontend
npm run test:watch
```

### Running Tests with Coverage

```bash
cd frontend
npm run test:coverage
```

### Running Tests with UI

```bash
cd frontend
npm run test:ui
```

### Test Configuration

- Vitest configuration is in `frontend/vitest.config.ts`
- Test files should be placed in `frontend/src/__tests__/` or use the
  `*.test.ts` / `*.spec.ts` naming convention
- Tests use jsdom for DOM simulation
- Global test functions (describe, it, expect) are available without imports

### Writing Tests

```typescript
import { describe, it, expect } from "vitest"
import { mount } from "@vue/test-utils"

describe("MyComponent", () => {
  it("should render correctly", () => {
    // Test code here
  })
})
```

## GitHub Actions

Both backend and frontend tests run automatically on:

- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop` branches
- Manual trigger via GitHub Actions UI

### Workflows

- **Backend Tests**: `.github/workflows/backend-tests.yml`
- **Frontend Tests**: `.github/workflows/frontend-tests.yml`

### Path Filtering

Workflows only run when files in their respective directories change:

- Backend workflow triggers on changes to `backend/**`
- Frontend workflow triggers on changes to `frontend/**`
- Both workflows also trigger on changes to their own workflow files
