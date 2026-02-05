# Implement tags and rules engine frontend

## User Story
**As a** user,
**I want to** create and manage tags and rules in the UI,
**So that** I can automatically categorize my transactions.

## Repo Notes
- Tags API exists (`/api/v1/tags`). Current tag model is label-only (no color field).
- Rules API does not exist yet (blocked on backend rules engine task).

## Scope

### Tags (Unblocked)
- List tags
- Create tag
- Rename tag
- Delete tag (with warning if in use)

### Rules (Blocked)
- Rule CRUD once `/api/v1/rules` exists
- Rule editor for conditions (payee/description/amount) and actions (add tag)

## Technical Implementation
- Add a dedicated view (recommended): `frontend/src/views/TagsView.vue` (or Settings sub-page).
- Add composables:
  - `frontend/src/composables/useTags.ts` for tag CRUD
  - `frontend/src/composables/useRules.ts` for rules CRUD (when backend exists)

## Dependencies
- Depends on backend "Create and finish tags and rule engine" for rules endpoints.

## Acceptance Criteria
- [ ] Tags CRUD fully functional
- [ ] Rules UI enabled once backend endpoints exist
- [ ] User can create a rule with conditions and tag action
- [ ] Rules can be applied to new uploads and via manual re-apply
