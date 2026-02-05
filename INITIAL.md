## User Story

**As a** user, **So that** I can view and analyze my spending across different
currencies in a consistent way. **I want to** have my transactions automatically
converted to a unified currency,

## Description

Credit card statements may contain transactions in multiple currencies (e.g.,
USD purchases on an ARS card). This task adds a currency conversion endpoint
that:

1. Converts transaction amounts to a unified/base currency for storage and
   analytics
2. Retrieves historical exchange rates for accurate conversion at transaction
   date
3. Allows displaying amounts in the original or converted currency as needed

## API Endpoint

### `POST /api/v1/currency/convert`

Convert an amount from one currency to another.

**Request Body:**

```json
{
  "amount": 150.0,
  "from_currency": "USD",
  "to_currency": "ARS",
  "date": "2024-01-15"
}
```

**Response:**

```json
{
  "original_amount": 150.0,
  "original_currency": "USD",
  "converted_amount": 127500.0,
  "target_currency": "ARS",
  "exchange_rate": 850.0,
  "rate_date": "2024-01-15"
}
```

### `GET /api/v1/currency/rates`

Get current or historical exchange rates.

**Query Parameters:**

- `base` (required) - Base currency code (e.g., "USD")
- `symbols` (optional) - Comma-separated target currencies (e.g., "ARS")
- `date` (optional) - Historical date for rates

## Technical Implementation

1. Create currency conversion service with exchange rate provider integration
   (e.g., BCRA API, Dolar API, or similar)
2. Implement rate caching to minimize API calls (rates don't change frequently)
3. Create database table for storing historical rates (fallback/offline support)
4. Add `/api/v1/currency/convert` endpoint
5. Add `/api/v1/currency/rates` endpoint
6. Consider adding a user preference for base/display currency

## Supported Currencies

- ARS (Argentine Peso)
- USD (US Dollar)

## Acceptance Criteria

- [ ] Convert endpoint accepts amount, source currency, target currency, and
      optional date
- [ ] Conversion uses historical rate when date is provided
- [ ] Rates endpoint returns current exchange rates for requested currencies
- [ ] Exchange rates are cached to reduce external API calls
- [ ] API returns appropriate errors for unsupported currencies
- [ ] Conversion is accurate to 2 decimal places for display currencies
- [ ] Endpoint handles external API failures gracefully (fallback to cached
      rates)
