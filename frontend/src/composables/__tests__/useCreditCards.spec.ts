import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useCreditCards, CardBrand, type CreditCard, type CreditCardCreate } from '../useCreditCards'

vi.mock('@/api', () => ({
  OpenAPI: {
    BASE: 'https://api.example.com',
    TOKEN: 'test-token',
  },
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

describe('useCreditCards', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    localStorage.clear()
  })

  it('requires authentication', async () => {
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
    localStorage.setItem('access_token', 'access-token')

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

    const input: CreditCardCreate = {
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
        body: JSON.stringify(input),
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
    localStorage.setItem('access_token', 'access-token')

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
})

