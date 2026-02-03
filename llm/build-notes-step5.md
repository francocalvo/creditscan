# Build Notes: Step 5 - Transactions Table

## Changes Made

Modified `frontend/src/components/StatementDetailModal.vue` to add a fully functional transactions table with loading, error, and empty states.

## Key Changes

### 1. Imports and Composable
- Added `watch` to Vue imports
- Imported `useStatementTransactions` composable
- Destructured: transactions, isLoading, error, fetchTransactions, reset

### 2. Watch Implementation
- Watches `props.visible` for changes
- On open + statement exists: calls `fetchTransactions(props.statement.id)`
- On close: calls `reset()` to clear transactions state

### 3. Helper Functions
- `formatTransactionDate(dateStr)`: Formats to "Jan 15, 2025" format
- `formatInstallments(cur, tot)`: Returns "X/Y" or "-"
- `handleRetry()`: Calls fetchTransactions for error recovery

### 4. Template Changes
Replaced placeholder with conditional rendering (v-if/v-else-if/v-else):
- **Loading state**: Spinner + "Loading transactions..." text
- **Error state**: pi-exclamation-circle icon + message + retry button
- **Empty state**: pi-inbox icon + "No transactions for this statement"
- **Table**: 6 columns (Date, Payee, Description, Amount, Installments, Tags)

### 5. Table Columns
- Date: formatTransactionDate(txn.txn_date)
- Payee: txn.payee
- Description: txn.description
- Amount: formatCurrency(txn.amount) with conditional color class (red for negative, green for positive)
- Installments: formatInstallments(txn.installment_cur, txn.installment_tot) - centered
- Tags: "-" placeholder (Step 8 adds actual tags)

### 6. CSS Styles Added
- `.loading-state`: Flex column, centered, spinner animation
- `.spinner`: 40px circle with border-top animation (spin keyframes)
- `.error-state`: Flex column, centered, red icon
- `.empty-state`: Flex column, centered, inbox icon
- `.transactions-table`: Full width, border-collapse, proper padding
- `.amount--negative`: Red color for negative amounts
- `.amount--positive`: Green color for positive amounts
- `.installments`: Centered text alignment
- `.tags`: Secondary color for placeholder

## Verification

- ✅ TypeScript type-check passes (vue-tsc --build)
- ✅ No new lint errors in StatementDetailModal.vue
- ✅ All acceptance criteria met:
  - Transactions fetched on modal open
  - Loading state displays
  - Transactions table renders with correct columns
  - Error state with retry button
  - Empty state with message
  - State resets on modal close
  - Installments format correctly (X/Y or "-")

## Notes

- Tags column shows "-" placeholder until Step 8 integrates actual tag display
- Table uses native HTML table element (not PrimeVue DataTable)
- Pagination will be added in Step 6
- Sorting will be added in Step 7
- Responsive design may need table horizontal scroll on mobile (Step 10)
