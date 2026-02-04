import { ref, computed } from 'vue'
import { OpenAPI, UsersService } from '@/api'
import { useCreditCards, type CreditCard } from './useCreditCards'
import { parseDateString } from '@/utils/date'
import type { ApiRequestOptions } from '@/api/core/ApiRequestOptions'

/**
 * Extended user type with preferred_currency field.
 * Used as a workaround until SDK types are regenerated.
 */
type UserPublicWithCurrency = {
  email: string
  is_active?: boolean
  is_superuser?: boolean
  full_name?: string | null
  id: string
  preferred_currency?: string | null
}

export interface CardStatement {
  id: string
  card_id: string
  period_start: string | null
  period_end: string | null
  close_date: string | null
  due_date: string | null
  previous_balance: number | null
  current_balance: number | null
  minimum_payment: number | null
  is_fully_paid: boolean
}

export interface StatementsResponse {
  data: CardStatement[]
  count: number
  pagination?: Record<string, number> | null
}

export type StatementStatus = 'paid' | 'pending' | 'overdue'

export interface StatementWithCard extends CardStatement {
  status: StatementStatus
  card?: CreditCard
}

export interface UserBalance {
  total_balance: number
  monthly_balance: number
}

export function useStatements() {
  const statements = ref<CardStatement[]>([])
  const balance = ref<UserBalance>({ total_balance: 0, monthly_balance: 0 })
  const isLoading = ref(false)
  const isBalanceLoading = ref(false)
  const error = ref<Error | null>(null)

  const { cards, fetchCards: fetchCreditCards } = useCreditCards()

  const targetCurrency = ref('ARS')
  let preferredCurrencyFetchInFlight: Promise<void> | null = null
  let preferredCurrencyLoaded = false

  const normalizeCurrencyCode = (currency: string) => currency.trim().toUpperCase()

  const isValidCurrency = (currency: string): boolean => {
    try {
      new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(0)
      return true
    } catch {
      return false
    }
  }

  const fetchPreferredCurrency = async () => {
    if (preferredCurrencyLoaded) return
    if (preferredCurrencyFetchInFlight) return preferredCurrencyFetchInFlight

    preferredCurrencyFetchInFlight = (async () => {
      try {
        const userResponse = await UsersService.readUserMe()
        const user = userResponse as UserPublicWithCurrency

        const currencyFromProfile = normalizeCurrencyCode(user.preferred_currency ?? 'ARS')
        targetCurrency.value = isValidCurrency(currencyFromProfile) ? currencyFromProfile : 'ARS'
      } catch (err) {
        console.warn('Failed to load preferred currency; falling back to ARS.', err)
        targetCurrency.value = 'ARS'
      } finally {
        preferredCurrencyLoaded = true
      }
    })().finally(() => {
      preferredCurrencyFetchInFlight = null
    })

    return preferredCurrencyFetchInFlight
  }

  const getStatementStatus = (statement: CardStatement): StatementStatus => {
    // Check if the statement is marked as fully paid in the API
    if (statement.is_fully_paid || statement.current_balance == 0.0) {
      return 'paid'
    }

    if (!statement.due_date) return 'pending'

    const dueDate = parseDateString(statement.due_date)
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    if (today > dueDate) {
      return 'overdue'
    }

    // Consider it paid if balance is 0 or negative (fallback check)
    if (statement.current_balance !== null && statement.current_balance <= 0) {
      return 'paid'
    }

    return 'pending'
  }

  const statementsWithCard = computed<StatementWithCard[]>(() => {
    const statusRank: Record<StatementStatus, number> = {
      overdue: 0,
      pending: 1,
      paid: 2,
    }

    return statements.value
      .map((statement) => {
        const card = cards.value.find((c) => c.id === statement.card_id)
        return {
          ...statement,
          status: getStatementStatus(statement),
          card,
        }
      })
      .sort((a, b) => {
        const statusDiff = statusRank[a.status] - statusRank[b.status]
        if (statusDiff !== 0) return statusDiff

        const aDueTime = a.due_date
          ? parseDateString(a.due_date).getTime()
          : Number.NEGATIVE_INFINITY
        const bDueTime = b.due_date
          ? parseDateString(b.due_date).getTime()
          : Number.NEGATIVE_INFINITY
        if (aDueTime !== bDueTime) return bDueTime - aDueTime

        return a.id.localeCompare(b.id)
      })
  })

  const fetchStatements = async (params?: { skip?: number; limit?: number; card_id?: string }) => {
    isLoading.value = true
    error.value = null

    try {
      await fetchPreferredCurrency()
      // First fetch credit cards so we can display card information
      await fetchCreditCards()

      // Then fetch statements
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'GET',
              url: '/api/v1/card-statements',
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''
      const queryParams = new URLSearchParams()

      if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
      if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
      if (params?.card_id) queryParams.append('card_id', params.card_id)

      const queryString = queryParams.toString()
      const url = `${OpenAPI.BASE}/api/v1/card-statements${queryString ? `?${queryString}` : ''}`

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch statements: ${response.statusText}`)
      }

      const data: StatementsResponse = await response.json()
      statements.value = data.data
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to fetch statements')
      console.error('Error fetching statements:', e)
    } finally {
      isLoading.value = false
    }
  }

  const formatCurrency = (amount: number | null): string => {
    const currency = isValidCurrency(targetCurrency.value) ? targetCurrency.value : 'USD'
    const safeAmount = amount === null ? 0 : Number.isFinite(amount) ? amount : 0
    const absAmount = Math.abs(safeAmount)

    const baseFractionDigits = currency === 'ARS' ? 0 : 2

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: baseFractionDigits,
      maximumFractionDigits: baseFractionDigits,
      ...(absAmount >= 1_000_000
        ? {
            notation: 'compact' as const,
            compactDisplay: 'short' as const,
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
          }
        : {}),
    }).format(safeAmount)
  }

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return 'N/A'
    const date = parseDateString(dateStr)
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
  }

  const formatPeriod = (startDate: string | null, endDate: string | null): string => {
    if (!startDate || !endDate) return 'N/A'
    const start = parseDateString(startDate)
    const end = parseDateString(endDate)

    if (start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear()) {
      return end.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    }

    return `${start.toLocaleDateString('en-US', { month: 'short' })} - ${end.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}`
  }

  const fetchBalance = async () => {
    isBalanceLoading.value = true
    error.value = null

    try {
      await fetchPreferredCurrency()
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'GET',
              url: '/api/v1/users/me/balance',
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''
      const url = `${OpenAPI.BASE}/api/v1/users/me/balance`

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch balance: ${response.statusText}`)
      }

      const data: UserBalance = await response.json()
      balance.value = data
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to fetch balance')
      console.error('Error fetching balance:', e)
    } finally {
      isBalanceLoading.value = false
    }
  }

  const createPayment = async (paymentData: {
    statement_id: string
    amount: number
    payment_date: string
    currency: string
  }) => {
    error.value = null

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'POST',
              url: '/api/v1/payments/',
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''
      const { useAuthStore } = await import('@/stores/auth')
      const authStore = useAuthStore()

      if (!authStore.user) {
        throw new Error('User not authenticated')
      }

      const url = `${OpenAPI.BASE}/api/v1/payments/`

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: authStore.user.id,
          statement_id: paymentData.statement_id,
          amount: paymentData.amount,
          payment_date: paymentData.payment_date,
          currency: paymentData.currency,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to create payment: ${response.statusText}`)
      }

      const data = await response.json()

      // Refresh statements and balance after successful payment
      await Promise.all([fetchStatements(), fetchBalance()])

      return data
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to create payment')
      console.error('Error creating payment:', e)
      throw error.value
    }
  }

  const updateStatement = async (
    statementId: string,
    updateData: Partial<{
      due_date: string | null
      close_date: string | null
      period_start: string | null
      period_end: string | null
      previous_balance: number | null
      current_balance: number | null
      minimum_payment: number | null
      is_fully_paid: boolean
    }>,
  ) => {
    error.value = null

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'PATCH',
              url: `/api/v1/card-statements/${statementId}`,
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''

      const url = `${OpenAPI.BASE}/api/v1/card-statements/${statementId}`

      const response = await fetch(url, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to update statement: ${response.statusText}`)
      }

      const updatedStatement = await response.json()

      // Update local statements array
      const index = statements.value.findIndex((s) => s.id === statementId)
      if (index !== -1) {
        statements.value[index] = { ...statements.value[index], ...updatedStatement }
      }

      return updatedStatement
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to update statement')
      console.error('Error updating statement:', e)
      throw error.value
    }
  }

  return {
    statements,
    statementsWithCard,
    cards,
    balance,
    isLoading,
    isBalanceLoading,
    error,
    fetchStatements,
    fetchBalance,
    createPayment,
    updateStatement,
    formatCurrency,
    formatDate,
    formatPeriod,
  }
}
