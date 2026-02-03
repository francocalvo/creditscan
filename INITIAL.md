# Create modal of statement details

**Status:** Not started
**Agent:** frontend

## User Story

**As a** user,
**I want to** click on a statement and see its full details in a modal,
**So that** I can review all transactions and information without leaving the dashboard.

## Repo Notes

- The Statements table already renders a "View Details" button in `frontend/src/views/StatementsView.vue`, but no modal exists yet.
- Backend endpoints needed for this modal already exist:
  - `GET /api/v1/card-statements/{statement_id}`
  - `GET /api/v1/transactions?statement_id={statement_id}`
  - Optional tags per transaction: `GET /api/v1/transaction-tags/transaction/{transaction_id}`

## Modal Content

### Header

- Card info (bank, brand, last4) derived from existing card list in `useStatements`.
- Statement period (start - end)
- Status badge (Paid/Pending/Overdue) using current frontend status logic.

### Summary

- Previous balance, current balance, minimum payment
- Due date, close date

### Transactions

- Table showing: Date, Payee, Description, Amount, Installments (if present)
- (Optional) Tags as chips (can be lazy-loaded per transaction)

### Actions

- Pay: open existing `frontend/src/components/PaymentModal.vue`
- Edit: enter edit mode (depends on the "edit from modal" task)
- Close: X / backdrop click

## Technical Implementation

1. Create `frontend/src/components/StatementDetailModal.vue` using PrimeVue `Dialog`.
2. Add selection state in `frontend/src/views/StatementsView.vue` (selected statement id + modal visible).
3. Fetch statement details and statement transactions using the endpoints above.
4. Enrich with card info from `cards` already loaded.

## Acceptance Criteria

- [ ] Modal opens from "View Details" and closes reliably
- [ ] Statement details are displayed
- [ ] Transactions are listed for the statement
- [ ] Pay action works via Payment modal
