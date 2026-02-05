import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useCreditCards, CardBrand, type CreditCard } from '../useCreditCards'

vi.mock('@/api', () => ({
  OpenAPI: {
    BASE: 'https://api.example.com',
    TOKEN: vi.fn().mockResolvedValue('test-token'),
  },
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn().mockReturnValue({
    user: { id: 'user-123' }
  })
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

describe('useCreditCards', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    localStorage.clear()
  })

  it('requires authentication (token)', async () => {
    const { OpenAPI } = await import('@/api')
    vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('')

    const { createCard } = useCreditCards()

    await expect(
      createCard({
        bank: 'Test Bank',
        brand: CardBrand.VISA,
        last4: '1234',
      })
    ).rejects.toThrow('Not authenticated')

    expect(mockFetch).not.toHaveBeenCalled()
  })

  it('POSTs to /api/v1/credit-cards/ and refreshes cards list', async () => {
    const { OpenAPI } = await import('@/api')
    vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')
    
    const createdCard: CreditCard = {
      id: 'card-123',
      user_id: 'user-123',
      bank: 'Test Bank',
      brand: CardBrand.VISA,
      last4: '1234',
      alias: 'Personal',
    }

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => createdCard,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ data: [createdCard], count: 1 }),
      })

    const { createCard, cards } = useCreditCards()

    const input = {
      bank: 'Test Bank',
      brand: CardBrand.VISA,
      last4: '1234',
      alias: 'Personal',
    }

    const result = await createCard(input)

    expect(result).toEqual(createdCard)

    expect(mockFetch).toHaveBeenNthCalledWith(
      1,
      'https://api.example.com/api/v1/credit-cards/',
      expect.objectContaining({
        method: 'POST',
        headers: {
          Authorization: 'Bearer access-token',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...input,
          user_id: 'user-123',
        }),
      })
    )

    expect(mockFetch).toHaveBeenNthCalledWith(
      2,
      'https://api.example.com/api/v1/credit-cards',
      expect.objectContaining({
        headers: {
          Authorization: 'Bearer test-token',
          'Content-Type': 'application/json',
        },
      })
    )

    expect(cards.value).toEqual([createdCard])
  })

  it('throws with server error message', async () => {
    const { OpenAPI } = await import('@/api')
    vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Invalid card data' }),
    })

    const { createCard, error } = useCreditCards()

    await expect(
      createCard({
        bank: 'Test Bank',
        brand: CardBrand.VISA,
        last4: '1234',
      })
    ).rejects.toThrow('Invalid card data')

    expect(error.value?.message).toBe('Invalid card data')
  })

  it('DELETEs /api/v1/credit-cards/{id} and removes card from state on 204', async () => {
    const { OpenAPI } = await import('@/api')
    vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')

    const card1: CreditCard = {
      id: 'card-1',
      user_id: 'user-123',
      bank: 'Test Bank',
      brand: CardBrand.VISA,
      last4: '1111',
    }
    const card2: CreditCard = {
      id: 'card-2',
      user_id: 'user-123',
      bank: 'Other Bank',
      brand: CardBrand.MASTERCARD,
      last4: '2222',
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
    })

    const { deleteCard, cards } = useCreditCards()
    cards.value = [card1, card2]

    await deleteCard('card-1')

    expect(mockFetch).toHaveBeenCalledWith(
      'https://api.example.com/api/v1/credit-cards/card-1',
      expect.objectContaining({
        method: 'DELETE',
        headers: {
          Authorization: 'Bearer access-token',
          'Content-Type': 'application/json',
        },
      })
    )

    expect(cards.value).toEqual([card2])
  })

  it('throws on delete error and preserves state', async () => {
    const { OpenAPI } = await import('@/api')
    vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')

    const card1: CreditCard = {
      id: 'card-1',
      user_id: 'user-123',
      bank: 'Test Bank',
      brand: CardBrand.VISA,
      last4: '1111',
    }

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Cannot delete card' }),
    })

    const { deleteCard, cards, error } = useCreditCards()
    cards.value = [card1]

    await expect(deleteCard('card-1')).rejects.toThrow('Cannot delete card')

    expect(cards.value).toEqual([card1])
    expect(error.value?.message).toBe('Cannot delete card')
  })
})
