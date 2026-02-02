---
status: pending
created: 2026-02-02
started: null
completed: null
---
# Task: Remove LRU Cache from Session Providers

## Description
Remove `@lru_cache` decorators from any provider functions that capture or return a Session. Update the provider pattern to thread sessions through the dependency graph so each request/test builds a fresh usecase graph bound to an injected session.

## Background
The `@lru_cache` decorator on provider functions causes sessions to be cached and reused across requests and tests. This breaks test isolation and prevents session injection. Providers should create fresh instances for each call, with the session passed through the entire graph.

## Reference Documentation
**Required:**
- Design: PROMPT.md (Milestone 2: True Injection, items 6 and 8)

**Note:** Read the design document before beginning implementation.

## Technical Requirements
1. Identify all `@lru_cache` decorated provider functions
2. Remove `@lru_cache` from providers that deal with sessions, repositories, or services
3. Update provider signatures to accept `session: Session` parameter
4. Thread the session through the provider dependency graph:
   - `provide_usecase(session)` → `provide_service(session)` → `provide_repo(session)`
5. Ensure providers that genuinely need caching (e.g., config) are separated from session-dependent ones

## Dependencies
- task-01-refactor-repositories must be completed
- Understanding of the provider module structure

## Implementation Approach
1. Search for `@lru_cache` in provider files
2. For each cached provider:
   ```python
   # Before
   @lru_cache
   def provide_user_service() -> UserService:
       repo = provide_user_repo()
       return UserService(repo)

   # After
   def provide_user_service(session: Session) -> UserService:
       repo = provide_user_repo(session)
       return UserService(repo)
   ```
3. Update the call chain to pass session from the top level (API route) down through all providers
4. If some providers need caching (settings, config), keep those separate with clear naming
5. Add tests verifying that calling a provider twice with different sessions returns different instances

## Acceptance Criteria

1. **No Cached Session Providers**
   - Given provider functions that return repositories or services
   - When I inspect their decorators
   - Then none have `@lru_cache` that would capture a session

2. **Session Threading**
   - Given a usecase provider function
   - When I call it with `session=test_session`
   - Then all nested providers (service, repo) receive the same session

3. **Fresh Instances Per Call**
   - Given a provider function called twice with different sessions
   - When I compare the returned instances
   - Then they are different objects bound to their respective sessions

4. **Request Isolation**
   - Given two concurrent API requests
   - When each gets its own session via dependency injection
   - Then their usecases/services/repos are isolated from each other

5. **Unit Tests**
   - Given provider functions with session parameters
   - When I test with injected sessions
   - Then each test gets isolated instances

## Metadata
- **Complexity**: High
- **Labels**: providers, dependency-injection, caching, refactoring
- **Required Skills**: Python, FastAPI dependencies, caching patterns
