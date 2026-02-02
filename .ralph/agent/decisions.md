# Decision Journal

## Template
```
## DEC-XXX: [Brief Title]
- **Decision**: [What was decided]
- **Chosen Option**: [Selected approach]
- **Confidence**: [0-100]
- **Alternatives Considered**: [Other options]
- **Reasoning**: [Why this choice]
- **Reversibility**: [Easy/Medium/Hard]
- **Timestamp**: [UTC ISO 8601]
```

---

## DEC-001: Test Isolation Strategy - Per-Test Transaction Rollback
- **Decision**: Use per-test transaction rollback instead of table truncation for test isolation
- **Chosen Option**: Transaction rollback with savepoints
- **Confidence**: 75
- **Alternatives Considered**:
  - Table truncation between tests (slower, simpler)
  - Fresh database per test (too slow)
  - No isolation, careful test ordering (fragile)
- **Reasoning**: Transaction rollback is faster than truncation, allows tests to run in parallel, and is the standard pattern for SQLAlchemy/SQLModel testing. The main risk is tests that rely on committed data for secondary connections, but our architecture uses single-session injection which avoids this.
- **Reversibility**: Easy - can switch to truncation if issues arise
- **Timestamp**: 2026-02-02T20:00:00Z

## DEC-002: Import Style for Test Utilities
- **Decision**: Use relative imports within the tests package
- **Chosen Option**: `from .utils.user import ...` style
- **Confidence**: 90
- **Alternatives Considered**:
  - Absolute imports with sys.path manipulation
  - Moving tests under app package
  - Using pytest plugins for path setup
- **Reasoning**: Relative imports are the standard Python pattern for intra-package imports. They work correctly when tests are run from the backend directory (which is the expected setup). No sys.path hacks needed.
- **Reversibility**: Easy
- **Timestamp**: 2026-02-02T20:00:00Z
