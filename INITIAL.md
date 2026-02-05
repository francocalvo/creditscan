# Delete cards from cards tab

## User Story
**As a** user,
**I want to** delete credit cards I no longer use,
**So that** my dashboard only shows relevant cards.

## Repo Notes
- Backend already exposes `DELETE /api/v1/credit-cards/{card_id}` (204 on success).
- Deleting a card that has statements/transactions may fail due to DB FK constraints; UX should warn before attempting delete.

## Implementation Plan
1. Add a delete action in the Cards tab UI (`frontend/src/views/StatementsView.vue`).
2. Show confirmation (PrimeVue ConfirmDialog or a simple confirm for MVP).
3. Before deleting, compute whether the card has related statements from already loaded data:
   - statements count: `statementsWithCard.filter(s => s.card_id === card.id).length`
   - show a stronger warning if > 0
4. Call `DELETE /api/v1/credit-cards/{card_id}`.
5. Refresh cards + statements lists after success; show toast on success/failure.

## Files
- `frontend/src/views/StatementsView.vue`
- `frontend/src/composables/useCreditCards.ts` (add delete mutation/helper)

## Acceptance Criteria
- [ ] Delete button available per card
- [ ] Confirmation shown
- [ ] Warning shown when card has statements
- [ ] Card removed from UI after successful delete
- [ ] Clear error shown if deletion fails
