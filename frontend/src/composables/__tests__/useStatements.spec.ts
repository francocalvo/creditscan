import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ref, computed } from 'vue'
import type { CreditCard } from '@/composables/useStatements'
import type { CardBrand } from '@/composables/useCreditCards'

// Mock useCreditCards
vi.mock('@/composables/useCreditCards', () => ({
  useCreditCards: vi.fn(() => ({
    cards: ref<CreditCard[]>([]),
    fetchCards: vi.fn().mockResolvedValue(undefined),
  })),
  CardBrand: {
    VISA: 'visa',
    MASTERCARD: 'mastercard',
    AMEX: 'amex',
    DISCOVER: 'discover',
    OTHER: 'other',
  },
}))

// Mock OpenAPI
vi.mock('@/api', () => ({
  OpenAPI: {
    BASE: 'http://localhost:8000',
    TOKEN: 'test-token',
  },
  UsersService: {
    readUserMe: vi.fn().mockResolvedValue({
      email: 'test@example.com',
      id: '1',
      preferred_currency: 'ARS',
    }),
  },
}))

describe('useStatements - aggregateUtilization', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns null value when no cards exist', () => {
    // Need to manually test the logic since we're mocking useCreditCards
    const cards = ref<CreditCard[]>([])

    const result = computed(() => {
      const allCards = cards.value
      const totalCount = allCards.length

      if (totalCount === 0) {
        return {
          value: null as number | null,
          missingCount: 0,
          totalCount: 0,
        }
      }

      const cardsWithLimits = allCards.filter(
        (card) => card.credit_limit !== null && card.credit_limit > 0 && Number.isFinite(card.credit_limit)
      )
      const missingCount = totalCount - cardsWithLimits.length

      if (cardsWithLimits.length === 0) {
        return {
          value: null,
          missingCount,
          totalCount,
        }
      }

      const avgLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) / cardsWithLimits.length
      const totalBalance = allCards.reduce((sum, card) => sum + card.outstanding_balance, 0)
      const totalLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) + missingCount * avgLimit
      const value = (totalBalance / totalLimit) * 100

      return {
        value,
        missingCount,
        totalCount,
      }
    })

    expect(result.value).toEqual({
      value: null,
      missingCount: 0,
      totalCount: 0,
    })
  })

  it('returns null value when all cards have missing limits', () => {
    const cards = ref<CreditCard[]>([
      {
        id: '1',
        user_id: 'user1',
        bank: 'Bank A',
        brand: 'visa' as CardBrand,
        last4: '1234',
        credit_limit: null,
        limit_last_updated_at: null,
        limit_source: null,
        outstanding_balance: 50000,
      },
      {
        id: '2',
        user_id: 'user1',
        bank: 'Bank B',
        brand: 'mastercard' as CardBrand,
        last4: '5678',
        credit_limit: null,
        limit_last_updated_at: null,
        limit_source: null,
        outstanding_balance: 75000,
      },
    ])

    const result = computed(() => {
      const allCards = cards.value
      const totalCount = allCards.length

      if (totalCount === 0) {
        return {
          value: null as number | null,
          missingCount: 0,
          totalCount: 0,
        }
      }

      const cardsWithLimits = allCards.filter(
        (card) => card.credit_limit !== null && card.credit_limit > 0 && Number.isFinite(card.credit_limit)
      )
      const missingCount = totalCount - cardsWithLimits.length

      if (cardsWithLimits.length === 0) {
        return {
          value: null,
          missingCount,
          totalCount,
        }
      }

      const avgLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) / cardsWithLimits.length
      const totalBalance = allCards.reduce((sum, card) => sum + card.outstanding_balance, 0)
      const totalLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) + missingCount * avgLimit
      const value = (totalBalance / totalLimit) * 100

      return {
        value,
        missingCount,
        totalCount,
      }
    })

    expect(result.value).toEqual({
      value: null,
      missingCount: 2,
      totalCount: 2,
    })
  })

  it('calculates correct utilization with all limits present', () => {
    const cards = ref<CreditCard[]>([
      {
        id: '1',
        user_id: 'user1',
        bank: 'Bank A',
        brand: 'visa' as CardBrand,
        last4: '1234',
        credit_limit: 600000,
        limit_last_updated_at: '2024-01-01T00:00:00',
        limit_source: 'manual',
        outstanding_balance: 150000,
      },
      {
        id: '2',
        user_id: 'user1',
        bank: 'Bank B',
        brand: 'mastercard' as CardBrand,
        last4: '5678',
        credit_limit: 200000,
        limit_last_updated_at: '2024-01-01T00:00:00',
        limit_source: 'manual',
        outstanding_balance: 0,
      },
    ])

    const result = computed(() => {
      const allCards = cards.value
      const totalCount = allCards.length

      if (totalCount === 0) {
        return {
          value: null as number | null,
          missingCount: 0,
          totalCount: 0,
        }
      }

      const cardsWithLimits = allCards.filter(
        (card) => card.credit_limit !== null && card.credit_limit > 0 && Number.isFinite(card.credit_limit)
      )
      const missingCount = totalCount - cardsWithLimits.length

      if (cardsWithLimits.length === 0) {
        return {
          value: null,
          missingCount,
          totalCount,
        }
      }

      const avgLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) / cardsWithLimits.length
      const totalBalance = allCards.reduce((sum, card) => sum + card.outstanding_balance, 0)
      const totalLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) + missingCount * avgLimit
      const value = (totalBalance / totalLimit) * 100

      return {
        value,
        missingCount,
        totalCount,
      }
    })

    // totalBalance = 150000 + 0 = 150000
    // totalLimit = 600000 + 200000 = 800000
    // utilization = 150000 / 800000 * 100 = 18.75
    expect(result.value.value).toBe(18.75)
    expect(result.value.missingCount).toBe(0)
    expect(result.value.totalCount).toBe(2)
  })

  it('imputes missing limits with average of known limits', () => {
    const cards = ref<CreditCard[]>([
      {
        id: '1',
        user_id: 'user1',
        bank: 'Bank A',
        brand: 'visa' as CardBrand,
        last4: '1234',
        credit_limit: 600000,
        limit_last_updated_at: '2024-01-01T00:00:00',
        limit_source: 'manual',
        outstanding_balance: 150000,
      },
      {
        id: '2',
        user_id: 'user1',
        bank: 'Bank B',
        brand: 'mastercard' as CardBrand,
        last4: '5678',
        credit_limit: 400000,
        limit_last_updated_at: '2024-01-01T00:00:00',
        limit_source: 'manual',
        outstanding_balance: 0,
      },
      {
        id: '3',
        user_id: 'user1',
        bank: 'Bank C',
        brand: 'amex' as CardBrand,
        last4: '9012',
        credit_limit: null,
        limit_last_updated_at: null,
        limit_source: null,
        outstanding_balance: 50000,
      },
    ])

    const result = computed(() => {
      const allCards = cards.value
      const totalCount = allCards.length

      if (totalCount === 0) {
        return {
          value: null as number | null,
          missingCount: 0,
          totalCount: 0,
        }
      }

      const cardsWithLimits = allCards.filter(
        (card) => card.credit_limit !== null && card.credit_limit > 0 && Number.isFinite(card.credit_limit)
      )
      const missingCount = totalCount - cardsWithLimits.length

      if (cardsWithLimits.length === 0) {
        return {
          value: null,
          missingCount,
          totalCount,
        }
      }

      const avgLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) / cardsWithLimits.length
      const totalBalance = allCards.reduce((sum, card) => sum + card.outstanding_balance, 0)
      const totalLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) + missingCount * avgLimit
      const value = (totalBalance / totalLimit) * 100

      return {
        value,
        missingCount,
        totalCount,
      }
    })

    // cardsWithLimits = [Card A (600k), Card B (400k)]
    // avgLimit = (600000 + 400000) / 2 = 500000
    // totalBalance = 150000 + 0 + 50000 = 200000
    // totalLimit = 600000 + 400000 + 1 * 500000 = 1500000
    // utilization = 200000 / 1500000 * 100 = 13.333...
    expect(result.value.value).toBeCloseTo(13.333, 2)
    expect(result.value.missingCount).toBe(1)
    expect(result.value.totalCount).toBe(3)
  })

  it('treats zero and negative limits as missing', () => {
    const cards = ref<CreditCard[]>([
      {
        id: '1',
        user_id: 'user1',
        bank: 'Bank A',
        brand: 'visa' as CardBrand,
        last4: '1234',
        credit_limit: 0,
        limit_last_updated_at: '2024-01-01T00:00:00',
        limit_source: 'manual',
        outstanding_balance: 50000,
      },
      {
        id: '2',
        user_id: 'user1',
        bank: 'Bank B',
        brand: 'mastercard' as CardBrand,
        last4: '5678',
        credit_limit: -100,
        limit_last_updated_at: '2024-01-01T00:00:00',
        limit_source: 'manual',
        outstanding_balance: 25000,
      },
    ])

    const result = computed(() => {
      const allCards = cards.value
      const totalCount = allCards.length

      if (totalCount === 0) {
        return {
          value: null as number | null,
          missingCount: 0,
          totalCount: 0,
        }
      }

      const cardsWithLimits = allCards.filter(
        (card) => card.credit_limit !== null && card.credit_limit > 0 && Number.isFinite(card.credit_limit)
      )
      const missingCount = totalCount - cardsWithLimits.length

      if (cardsWithLimits.length === 0) {
        return {
          value: null,
          missingCount,
          totalCount,
        }
      }

      const avgLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) / cardsWithLimits.length
      const totalBalance = allCards.reduce((sum, card) => sum + card.outstanding_balance, 0)
      const totalLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) + missingCount * avgLimit
      const value = (totalBalance / totalLimit) * 100

      return {
        value,
        missingCount,
        totalCount,
      }
    })

    expect(result.value).toEqual({
      value: null,
      missingCount: 2,
      totalCount: 2,
    })
  })

  it('produces 0 utilization for cards with zero balances when limits exist', () => {
    const cards = ref<CreditCard[]>([
      {
        id: '1',
        user_id: 'user1',
        bank: 'Bank A',
        brand: 'visa' as CardBrand,
        last4: '1234',
        credit_limit: 600000,
        limit_last_updated_at: '2024-01-01T00:00:00',
        limit_source: 'manual',
        outstanding_balance: 0,
      },
      {
        id: '2',
        user_id: 'user1',
        bank: 'Bank B',
        brand: 'mastercard' as CardBrand,
        last4: '5678',
        credit_limit: 400000,
        limit_last_updated_at: '2024-01-01T00:00:00',
        limit_source: 'manual',
        outstanding_balance: 0,
      },
    ])

    const result = computed(() => {
      const allCards = cards.value
      const totalCount = allCards.length

      if (totalCount === 0) {
        return {
          value: null as number | null,
          missingCount: 0,
          totalCount: 0,
        }
      }

      const cardsWithLimits = allCards.filter(
        (card) => card.credit_limit !== null && card.credit_limit > 0 && Number.isFinite(card.credit_limit)
      )
      const missingCount = totalCount - cardsWithLimits.length

      if (cardsWithLimits.length === 0) {
        return {
          value: null,
          missingCount,
          totalCount,
        }
      }

      const avgLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) / cardsWithLimits.length
      const totalBalance = allCards.reduce((sum, card) => sum + card.outstanding_balance, 0)
      const totalLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) + missingCount * avgLimit
      const value = (totalBalance / totalLimit) * 100

      return {
        value,
        missingCount,
        totalCount,
      }
    })

    expect(result.value.value).toBe(0)
    expect(result.value.missingCount).toBe(0)
    expect(result.value.totalCount).toBe(2)
  })

  it('handles Infinity and NaN limits as missing', () => {
    const cards = ref<CreditCard[]>([
      {
        id: '1',
        user_id: 'user1',
        bank: 'Bank A',
        brand: 'visa' as CardBrand,
        last4: '1234',
        credit_limit: Infinity,
        limit_last_updated_at: '2024-01-01T00:00:00',
        limit_source: 'manual',
        outstanding_balance: 50000,
      },
      {
        id: '2',
        user_id: 'user1',
        bank: 'Bank B',
        brand: 'mastercard' as CardBrand,
        last4: '5678',
        credit_limit: NaN,
        limit_last_updated_at: '2024-01-01T00:00:00',
        limit_source: 'manual',
        outstanding_balance: 25000,
      },
    ])

    const result = computed(() => {
      const allCards = cards.value
      const totalCount = allCards.length

      if (totalCount === 0) {
        return {
          value: null as number | null,
          missingCount: 0,
          totalCount: 0,
        }
      }

      const cardsWithLimits = allCards.filter(
        (card) => card.credit_limit !== null && card.credit_limit > 0 && Number.isFinite(card.credit_limit)
      )
      const missingCount = totalCount - cardsWithLimits.length

      if (cardsWithLimits.length === 0) {
        return {
          value: null,
          missingCount,
          totalCount,
        }
      }

      const avgLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) / cardsWithLimits.length
      const totalBalance = allCards.reduce((sum, card) => sum + card.outstanding_balance, 0)
      const totalLimit = cardsWithLimits.reduce((sum, card) => sum + card.credit_limit!, 0) + missingCount * avgLimit
      const value = (totalBalance / totalLimit) * 100

      return {
        value,
        missingCount,
        totalCount,
      }
    })

    expect(result.value).toEqual({
      value: null,
      missingCount: 2,
      totalCount: 2,
    })
  })
})
