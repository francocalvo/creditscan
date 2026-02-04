/**
 * Composable for fetching transactions filtered by statement ID.
 *
 * Provides methods to fetch transactions with pagination support.
 * Useful for displaying paginated transaction lists in statement detail modals.
 */
import { ref } from 'vue'
import { OpenAPI } from '@/api'
import type { ApiRequestOptions } from '@/api/core/ApiRequestOptions'

export interface StatementTransaction {
  id: string
  statement_id: string
  txn_date: string
  payee: string
  description: string
  amount: number
  currency: string
  coupon: string | null
  installment_cur: number | null
  installment_tot: number | null
}

export interface TransactionsResponse {
  data: StatementTransaction[]
  count: number
}

export interface TransactionUpdate {
  txn_date?: string
  payee?: string
  description?: string
  amount?: number
  currency?: string
  coupon?: string | null
  installment_cur?: number | null
  installment_tot?: number | null
}

export interface TransactionCreate {
  statement_id: string
  txn_date: string
  payee: string
  description: string
  amount: number
  currency: string
  coupon?: string | null
  installment_cur?: number | null
  installment_tot?: number | null
}

export function useStatementTransactions() {
  const transactions = ref<StatementTransaction[]>([])
  const totalCount = ref<number>(0)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  /**
   * Fetches transactions for a specific statement with pagination options.
   *
   * @param statementId - The ID of the statement to fetch transactions for
   * @param options - Optional pagination parameters (skip and limit)
   */
  const fetchTransactions = async (
    statementId: string,
    options?: { skip?: number; limit?: number },
  ) => {
    isLoading.value = true
    error.value = null

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'GET',
              url: '/api/v1/transactions',
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''

      const queryParams = new URLSearchParams()
      queryParams.append('statement_id', statementId)

      if (options?.skip !== undefined) {
        queryParams.append('skip', options.skip.toString())
      }
      if (options?.limit !== undefined) {
        queryParams.append('limit', options.limit.toString())
      }

      const queryString = queryParams.toString()
      const url = `${OpenAPI.BASE}/api/v1/transactions/${queryString ? `?${queryString}` : ''}`

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch transactions: ${response.statusText}`)
      }

      const data: TransactionsResponse = await response.json()
      transactions.value = data.data
      totalCount.value = data.count
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to fetch transactions')
      console.error('Error fetching transactions:', e)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Clears all transactions and resets state.
   */
  const reset = () => {
    transactions.value = []
    totalCount.value = 0
    error.value = null
  }

  /**
   * Updates an existing transaction.
   *
   * @param transactionId - The ID of the transaction to update
   * @param updateData - Partial transaction data to update
   * @returns The updated transaction
   */
  const updateTransaction = async (transactionId: string, updateData: TransactionUpdate) => {
    error.value = null

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'PATCH',
              url: `/api/v1/transactions/${transactionId}`,
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''

      const url = `${OpenAPI.BASE}/api/v1/transactions/${transactionId}`

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
        throw new Error(errorData.detail || `Failed to update transaction: ${response.statusText}`)
      }

      const updatedTransaction = await response.json()

      // Update local transactions array
      const index = transactions.value.findIndex((t) => t.id === transactionId)
      if (index !== -1) {
        transactions.value[index] = { ...transactions.value[index], ...updatedTransaction }
      }

      return updatedTransaction
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to update transaction')
      console.error('Error updating transaction:', e)
      throw error.value
    }
  }

  /**
   * Creates a new transaction.
   *
   * @param createData - Transaction data to create
   * @returns The created transaction
   */
  const createTransaction = async (createData: TransactionCreate) => {
    error.value = null

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'POST',
              url: '/api/v1/transactions/',
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''

      const url = `${OpenAPI.BASE}/api/v1/transactions/`

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(createData),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to create transaction: ${response.statusText}`)
      }

      const createdTransaction = await response.json()

      // Add to local transactions array
      transactions.value.push(createdTransaction)
      totalCount.value += 1

      return createdTransaction
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to create transaction')
      console.error('Error creating transaction:', e)
      throw error.value
    }
  }

  /**
   * Deletes a transaction.
   *
   * @param transactionId - The ID of the transaction to delete
   */
  const deleteTransaction = async (transactionId: string) => {
    error.value = null

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'DELETE',
              url: `/api/v1/transactions/${transactionId}`,
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''

      const url = `${OpenAPI.BASE}/api/v1/transactions/${transactionId}`

      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to delete transaction: ${response.statusText}`)
      }

      // Remove from local transactions array
      const index = transactions.value.findIndex((t) => t.id === transactionId)
      if (index !== -1) {
        transactions.value.splice(index, 1)
        totalCount.value -= 1
      }

      return true
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to delete transaction')
      console.error('Error deleting transaction:', e)
      throw error.value
    }
  }

  return {
    transactions,
    totalCount,
    isLoading,
    error,
    fetchTransactions,
    reset,
    updateTransaction,
    createTransaction,
    deleteTransaction,
  }
}
