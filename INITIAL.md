# Add credit limits and real credit utilization

## User Story
**As a** user,
**I want** the system to track credit limits per card and calculate real credit utilization,
**So that** I can trust the dashboard metrics and understand my actual credit usage.

## Repo Notes
- Credit cards exist in `credit_cards` table but do not currently store `credit_limit`.
- Statement upload endpoint parses JSON but does not extract/update credit limits.
- Dashboard currently shows hardcoded or mocked utilization percentages.
- Currency handling exists for transactions; similar approach needed for limits.

## Goal
Store per-card credit limits and compute Credit Utilization from real data. Auto-update limits when present in uploaded statement JSON, with safeguards against older statements overwriting newer data.

## Database Changes
- Add to `credit_cards` table:
  - `credit_limit` (Decimal, nullable)
  - `credit_limit_currency` (String, nullable) — or use card's existing currency
  - `limit_last_updated_at` (DateTime, nullable)
  - `limit_source` (Enum: `manual` | `statement`)

## API Changes
- `PATCH /api/v1/credit-cards/{card_id}` — allow setting `credit_limit` manually (sets `limit_source=manual`)
- Statement ingestion: if JSON includes credit limit field, update card's limit only if:
  - Card has no limit set, OR
  - Statement date > `limit_last_updated_at`

## Credit Utilization Calculation
- Per card: `current_balance / credit_limit * 100`
- Aggregate: sum of balances / sum of limits
- If any card is missing a limit: show "N/A" with prompt to add limits

## Open Questions
- Exact JSON field name for credit limit in statement payload (e.g., `credit_limit`, `limite_credito`).
- Currency rule: store limit in card's currency vs. convert to user's preferred currency.

## Acceptance Criteria
- [ ] `credit_cards` table has `credit_limit`, `limit_last_updated_at`, `limit_source` columns
- [ ] Manual edit of credit limit via API works and sets `limit_source=manual`
- [ ] Statement upload with credit limit updates card's limit (if newer)
- [ ] Older statement uploads do not overwrite newer limits
- [ ] Credit Utilization endpoint/calculation returns real % when all cards have limits
- [ ] Credit Utilization returns N/A (or equivalent) when limits are missing/partial
- [ ] Tests cover limit update logic and utilization calculation
