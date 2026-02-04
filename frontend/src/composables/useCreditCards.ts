import { ref } from 'vue'
import { OpenAPI } from '@/api'
import type { ApiRequestOptions } from '@/api/core/ApiRequestOptions'

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
}

export interface CreditCardsResponse {
  data: CreditCard[]
  count: number
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

      const data: CreditCardsResponse = await response.json()
      cards.value = data.data
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

  return {
    cards,
    isLoading,
    error,
    fetchCards,
    getCardById,
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
