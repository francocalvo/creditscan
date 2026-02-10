import type { BatchCurrencyConversionResponse, CurrencyConversionRequest } from './types.gen'
import { CurrencyService } from './services.gen'
import type { CancelablePromise } from './core/CancelablePromise'

export type { BatchCurrencyConversionResponse, CurrencyConversionRequest } from './types.gen'
export { CurrencyService } from './services.gen'

export function parseDecimal(value: number | string | null | undefined): number {
  if (value === null || value === undefined) return 0
  if (typeof value === 'number') return Number.isFinite(value) ? value : 0

  const normalized = value.replace(/,/g, '').trim()
  if (normalized === '') return 0

  const parsed = Number.parseFloat(normalized)
  return Number.isFinite(parsed) ? parsed : 0
}

export function convertCurrencyBatch(params: {
  conversions: CurrencyConversionRequest[]
  date?: string | null
}): CancelablePromise<BatchCurrencyConversionResponse> {
  return CurrencyService.currencyConvertCurrencyBatch({
    requestBody: { conversions: params.conversions },
    date: params.date ?? undefined,
  })
}
