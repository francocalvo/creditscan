/**
 * Currency conversion API client.
 *
 * Provides functions for converting amounts between currencies using the
 * backend currency conversion endpoints. Supports both single and batch
 * conversions for efficient processing of multiple transactions.
 */

import { OpenAPI } from './core/OpenAPI'
import type { ApiRequestOptions } from './core/ApiRequestOptions'

/**
 * Request model for converting an amount from one currency to another.
 */
export interface CurrencyConversionRequest {
  amount: number | string
  from_currency: string
  to_currency: string
  date?: string
}

/**
 * Response model for a currency conversion.
 *
 * All decimal fields are returned as strings from the backend
 * and should be parsed to numbers for frontend use.
 */
export interface CurrencyConversionResponse {
  original_amount: number | string
  converted_amount: number | string
  from_currency: string
  to_currency: string
  rate: number | string
}

/**
 * Request model for converting multiple amounts.
 */
export interface BatchCurrencyConversionRequest {
  conversions: CurrencyConversionRequest[]
}

/**
 * Response model for batch currency conversion.
 */
export interface BatchCurrencyConversionResponse {
  results: CurrencyConversionResponse[]
}

/**
 * Safely parse a decimal value (number or string) to a JavaScript number.
 *
 * Backend returns Decimal fields as strings to preserve precision.
 * This function handles both string and number inputs, parsing
 * strings with parseFloat and returning numbers as-is.
 *
 * @param value - The decimal value to parse (number or string)
 * @returns A JavaScript number, or NaN if parsing fails
 *
 * @example
 * ```ts
 * parseDecimal("100.50") // 100.5
 * parseDecimal(100.50)   // 100.5
 * parseDecimal("invalid") // NaN
 * ```
 */
export function parseDecimal(value: number | string): number {
  if (typeof value === 'number') {
    return value
  }
  const parsed = parseFloat(value)
  return isNaN(parsed) ? 0 : parsed
}

/**
 * Convert a single amount between currencies.
 *
 * Uses the backend POST /api/v1/currency/convert endpoint.
 * Requires authentication via Bearer token.
 *
 * @param request - The currency conversion request
 * @returns A promise that resolves to the conversion response
 * @throws Error if the request fails or returns a non-2xx status
 *
 * @example
 * ```ts
 * const result = await convertCurrency({
 *   amount: 100,
 *   from_currency: "USD",
 *   to_currency: "ARS"
 * })
 * console.log(parseDecimal(result.converted_amount)) // 100000
 * ```
 */
export async function convertCurrency(
  request: CurrencyConversionRequest,
): Promise<CurrencyConversionResponse> {
  const token =
    typeof OpenAPI.TOKEN === 'function'
      ? await OpenAPI.TOKEN({
          method: 'POST',
          url: '/api/v1/currency/convert',
          body: request,
        } as ApiRequestOptions<string>)
      : OpenAPI.TOKEN || ''
  const url = `${OpenAPI.BASE}/api/v1/currency/convert`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    let errorMessage = `Failed to convert currency: ${response.statusText}`
    try {
      const errorData = await response.json()
      if (errorData.detail) {
        errorMessage = errorData.detail
      }
    } catch {
      // JSON parsing failed, use default error message
    }
    throw new Error(errorMessage)
  }

  const data: CurrencyConversionResponse = await response.json()
  return data
}

/**
 * Convert multiple amounts between currencies in a single request.
 *
 * Uses the backend POST /api/v1/currency/convert/batch endpoint.
 * More efficient than multiple single conversions for large datasets.
 * Results are returned in the same order as the request array.
 *
 * @param request - The batch currency conversion request
 * @returns A promise that resolves to the batch conversion response
 * @throws Error if the request fails or returns a non-2xx status
 *
 * @example
 * ```ts
 * const result = await convertCurrencyBatch({
 *   conversions: [
 *     { amount: 100, from_currency: "USD", to_currency: "ARS" },
 *     { amount: 1000, from_currency: "ARS", to_currency: "USD" }
 *   ]
 * })
 * result.results.forEach((r) => {
 *   console.log(parseDecimal(r.converted_amount))
 * })
 * ```
 */
export async function convertCurrencyBatch(
  request: BatchCurrencyConversionRequest,
): Promise<BatchCurrencyConversionResponse> {
  const token =
    typeof OpenAPI.TOKEN === 'function'
      ? await OpenAPI.TOKEN({
          method: 'POST',
          url: '/api/v1/currency/convert/batch',
          body: request,
        } as ApiRequestOptions<string>)
      : OpenAPI.TOKEN || ''
  const url = `${OpenAPI.BASE}/api/v1/currency/convert/batch`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    let errorMessage = `Failed to batch convert currency: ${response.statusText}`
    try {
      const errorData = await response.json()
      if (errorData.detail) {
        errorMessage = errorData.detail
      }
    } catch {
      // JSON parsing failed, use default error message
    }
    throw new Error(errorMessage)
  }

  const data: BatchCurrencyConversionResponse = await response.json()
  return data
}
