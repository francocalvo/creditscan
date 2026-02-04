## User Story
**As a** user,
**I want to** see detailed financial analytics,
**So that** I can understand my spending patterns and make better financial decisions.

## Repo Notes
- The Analytics tab currently exists as a placeholder in `frontend/src/views/StatementsView.vue`.
- Backend currently does not expose analytics aggregation endpoints.
- Backend *does* expose `GET /api/v1/transactions` with `skip`/`limit`.

## MVP Approach (No new backend endpoints)
- Build charts based on the most recent N transactions fetched via `GET /api/v1/transactions`.
- Add simple date-range UI client-side; if server-side filtering is needed later, extend the transactions endpoint.

## Future (Backend-supported)
- Add aggregation endpoints when data volume makes client-side aggregation too expensive:
	- `GET /api/v1/analytics/spending-by-month`
	- `GET /api/v1/analytics/spending-by-tag`
	- `GET /api/v1/analytics/top-merchants`

## Technical Implementation
- Use PrimeVue Chart components.
- Create `frontend/src/composables/useAnalytics.ts` for aggregation logic + loading states.

## Acceptance Criteria
- [ ] Monthly spending chart displayed
- [ ] Spending by tag/category chart displayed (based on available data)
- [ ] Top merchants list
- [ ] Loading/empty states handled
