---
status: pending
created: 2026-02-02
started: null
completed: null
---
# Task: Fix Model Mutations and Standardize Patterns

## Description
Fix routes that incorrectly mutate public/response models instead of ORM models. Standardize the pattern: repositories handle ORM mutations, services/usecases return public models.

## Background
Some routes (e.g., `app/api/routes/login.py:reset_password`) mutate a `UserPublic` model directly, which doesn't persist to the database. The correct pattern is to load the ORM model via repository, mutate it, save via repository, then convert to public model for response.

## Reference Documentation
**Required:**
- Design: PROMPT.md (Milestone 3: Make API Routes Consume SessionDep, items 10-11)

**Note:** Read the design document before beginning implementation.

## Technical Requirements
1. Identify routes that mutate public/response models (`*Public`, `*Response`, `*Out`)
2. Fix each to use the correct pattern:
   - Load ORM model from repository
   - Perform mutations on ORM model
   - Save via repository
   - Convert to public model for response
3. Ensure clear separation: repositories return ORM models, services/usecases return public models
4. Update type hints to reflect the correct model types at each layer

## Dependencies
- task-01-inject-session-in-routes should be completed or in progress
- Understanding of the model hierarchy (ORM vs public models)

## Implementation Approach
1. Search for patterns like `user_public.field = value` in route files
2. For each violation, refactor:
   ```python
   # Before (WRONG - mutating public model)
   @router.post("/reset-password")
   def reset_password(body: ResetPasswordRequest, session: SessionDep):
       user_public = get_user_by_email(body.email)
       user_public.hashed_password = hash_password(body.new_password)  # Won't persist!
       return user_public

   # After (CORRECT - mutating ORM model via repository)
   @router.post("/reset-password")
   def reset_password(body: ResetPasswordRequest, session: SessionDep):
       user_repo = provide_user_repo(session)
       user = user_repo.get_by_email(body.email)
       if not user:
           raise HTTPException(404)
       user.hashed_password = hash_password(body.new_password)
       user_repo.save(user)
       return UserPublic.model_validate(user)
   ```
3. Document the pattern in code comments or a conventions file
4. Add tests verifying mutations persist to the database

## Acceptance Criteria

1. **No Public Model Mutations**
   - Given the route codebase
   - When I search for mutations on `*Public` or `*Response` models
   - Then no mutations are found (only reads/returns)

2. **Repository Handles ORM**
   - Given a route that modifies data
   - When I trace the mutation
   - Then it happens on an ORM model obtained from a repository

3. **Persistence Verified**
   - Given the `reset_password` endpoint (or similar)
   - When I call it to change a password
   - Then the change is persisted and a subsequent login works with the new password

4. **Clear Layer Separation**
   - Given repository methods
   - When I check their return types
   - Then they return ORM models (not public models)

5. **Unit Tests**
   - Given routes that mutate data
   - When I test them with an injected session
   - Then changes persist and can be verified via queries

## Metadata
- **Complexity**: Medium
- **Labels**: api, models, refactoring, patterns
- **Required Skills**: Python, SQLModel, FastAPI, ORM patterns
