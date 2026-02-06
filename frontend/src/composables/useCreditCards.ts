import { ref } from 'vue'
import { OpenAPI } from '@/api'
import type { ApiRequestOptions } from '@/api/core/ApiRequestOptions'
import { useAuthStore } from '@/stores/auth'

export enum CardBrand {
  VISA = 'visa',
  MASTERCARD = 'mastercard',
  AMEX = 'amex',
  DISCOVER = 'discover',
  OTHER = 'other',
}

export interface CreditCard {
  id: string
  user_id: string
  bank: string
  brand: CardBrand
  last4: string
  credit_limit: number | null
  limit_last_updated_at: string | null
  limit_source: 'manual' | 'statement' | null
  outstanding_balance: number
  alias?: string
}

export interface CreditCardCreate {
  user_id: string
  bank: string
  brand: CardBrand
  last4: string
  alias?: string
}

export interface CreditCardsResponse {
  data: CreditCard[]
  count: number
}

type CreditCardApi = Omit<CreditCard, 'credit_limit' | 'outstanding_balance'> & {
  credit_limit: number | string | null
  outstanding_balance: number | string
}

type CreditCardsResponseApi = Omit<CreditCardsResponse, 'data'> & {
  data: CreditCardApi[]
}

const toFiniteNumberOrNull = (value: unknown): number | null => {
  if (value === null || value === undefined) return null

  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null
  }

  if (typeof value === 'string') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }

  return null
}

const toFiniteNumber = (value: unknown, fallback: number): number => {
  return toFiniteNumberOrNull(value) ?? fallback
}

const normalizeCard = (card: CreditCardApi): CreditCard => {
  return {
    ...card,
    credit_limit: toFiniteNumberOrNull(card.credit_limit),
    outstanding_balance: toFiniteNumber(card.outstanding_balance, 0),
  }
}

export function useCreditCards() {
  const cards = ref<CreditCard[]>([])
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  const fetchCards = async (params?: { skip?: number; limit?: number; user_id?: string }) => {
    isLoading.value = true
    error.value = null

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'GET',
              url: '/api/v1/credit-cards',
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''
      const queryParams = new URLSearchParams()

      if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
      if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
      if (params?.user_id) queryParams.append('user_id', params.user_id)

      const queryString = queryParams.toString()
      const url = `${OpenAPI.BASE}/api/v1/credit-cards${queryString ? `?${queryString}` : ''}`

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch credit cards: ${response.statusText}`)
      }

      const data: CreditCardsResponseApi = await response.json()
      cards.value = data.data.map(normalizeCard)
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to fetch credit cards')
      console.error('Error fetching credit cards:', e)
    } finally {
      isLoading.value = false
    }
  }

  const getCardById = (cardId: string): CreditCard | undefined => {
    return cards.value.find((card) => card.id === cardId)
  }

  /**
   * Create a new credit card for the current user and refresh the local cards list.
   */
  const createCard = async (cardData: Omit<CreditCardCreate, 'user_id'>): Promise<CreditCard> => {
    error.value = null

    const authStore = useAuthStore()
    if (!authStore.user?.id) {
      const authError = new Error('User not loaded')
      error.value = authError
      throw authError
    }

    const token =
      typeof OpenAPI.TOKEN === 'function'
        ? await OpenAPI.TOKEN({
            method: 'POST',
            url: '/api/v1/credit-cards/',
          } as ApiRequestOptions<string>)
        : OpenAPI.TOKEN || ''

    if (!token) {
      const authError = new Error('Not authenticated')
      error.value = authError
      throw authError
    }

    const url = `${OpenAPI.BASE}/api/v1/credit-cards/`

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...cardData,
          user_id: authStore.user.id,
        }),
      })

      if (!response.ok) {
        let message = 'Failed to create credit card'
        try {
          const body: unknown = await response.json()
          if (typeof body === 'object' && body !== null && 'detail' in body) {
            const detail = (body as { detail?: unknown }).detail
            if (typeof detail === 'string' && detail.trim()) {
              message = detail
            } else if (Array.isArray(detail)) {
              const firstMessage = detail
                .map((item) => {
                  if (typeof item === 'string') return item
                  if (typeof item === 'object' && item !== null && 'msg' in item) {
                    const msg = (item as { msg?: unknown }).msg
                    return typeof msg === 'string' ? msg : ''
                  }
                  return ''
                })
                .find((msg) => msg.trim())
              if (firstMessage) message = firstMessage
            }
          }
        } catch {
          // ignore JSON parsing errors and fall back to default message
        }

        throw new Error(message)
      }

      const createdCardApi: CreditCardApi = await response.json()
      const createdCard: CreditCard = normalizeCard(createdCardApi)
      await fetchCards()
      return createdCard
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Failed to create credit card')
      error.value = err
      throw err
    }
  }

  /**
   * Delete a credit card by id and update the local cards list on success.
   */
  const deleteCard = async (cardId: string): Promise<void> => {
    error.value = null

    const token =
      typeof OpenAPI.TOKEN === 'function'
        ? await OpenAPI.TOKEN({
            method: 'DELETE',
            url: `/api/v1/credit-cards/${cardId}`,
          } as ApiRequestOptions<string>)
        : OpenAPI.TOKEN || ''

    if (!token) {
      const authError = new Error('Not authenticated')
      error.value = authError
      throw authError
    }

    const url = `${OpenAPI.BASE}/api/v1/credit-cards/${cardId}`

    try {
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.status === 204) {
        cards.value = cards.value.filter((card) => card.id !== cardId)
        return
      }

      if (!response.ok) {
        let message = 'Failed to delete credit card'
        try {
          const body: unknown = await response.json()
          if (typeof body === 'object' && body !== null && 'detail' in body) {
            const detail = (body as { detail?: unknown }).detail
            if (typeof detail === 'string' && detail.trim()) {
              message = detail
            }
          }
        } catch {
          // ignore JSON parsing errors and fall back to default message
        }

        throw new Error(message)
      }

      cards.value = cards.value.filter((card) => card.id !== cardId)
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Failed to delete credit card')
      error.value = err
      throw err
    }
  }

  return {
    cards,
    isLoading,
    error,
    fetchCards,
    getCardById,
    createCard,
    deleteCard,
  }
}

// Utility functions that can be used outside the composable
export const getCardDisplayName = (card: CreditCard): string => {
  const brandName = card.brand.charAt(0).toUpperCase() + card.brand.slice(1)
  return `${card.bank} ${brandName}`
}

export const getCardWithLast4 = (card: CreditCard): string => {
  return `${getCardDisplayName(card)} ••${card.last4}`
}
