# Implement upload statement workflow

**Status:** In progress
**Agent:** backend

## User Story

**As a** user,
**I want to** upload a PDF credit card statement,
**So that** the system automatically extracts and stores all my transactions without manual data entry.

## Repo Notes

- Backend already has JSON CRUD endpoints for statements + transactions:
  - `POST /api/v1/card-statements/`
  - `POST /api/v1/transactions/`
- There is currently **no** PDF upload endpoint.
- Tagging infrastructure exists (`tags` + `transaction_tags` domains), but automatic rules do not yet exist.

## Proposed Backend API

- `POST /api/v1/card-statements/upload`
  - Accept `multipart/form-data` with `card_id` and `file` (PDF)
  - Create a `CardStatement` and associated `Transaction` rows
  - Apply rules (once rules engine exists) by creating `TransactionTag` rows
  - Return created statement + transaction count

## Extraction Requirements

- Extract statement metadata:
  - period start/end, close date, due date
  - previous/current balance, minimum payment
- Extract transactions:
  - txn_date, payee, description, amount, currency
  - installments (`installment_cur`/`installment_tot`) when present

## Implementation Notes

- Start with one supported PDF format (define a "supported" bank/brand) and return a clear 400/422 for unsupported PDFs.
- Prefer a single DB transaction for statement + transactions creation.
- Add structured error handling and logging.

## Dependencies

- Depends on backend rules engine for auto-tagging after upload.

## Acceptance Criteria

- [ ] PDF upload endpoint exists and accepts a PDF
- [ ] Statement metadata extracted and stored
- [ ] Transactions created with correct dates/amounts
- [ ] Installments stored when present
- [ ] (When rules exist) tags auto-applied
- [ ] Clear errors for unsupported formats
