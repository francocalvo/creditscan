import { ref } from 'vue'
import { OpenAPI } from '@/api'

interface StatementTransaction {
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

export function useStatementTransactions() {
  const transactions = ref<StatementTransaction[]>([])
  const totalCount = ref<number>(0)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  const fetchTransactions = async (
    statementId: string,
    options?: { skip?: number; limit?: number }
  ) => {
    isLoading.value = true
    error.value = null

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function' ? await OpenAPI.TOKEN({} as any) : OpenAPI.TOKEN || ''

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

  const reset = () => {
    transactions.value = []
    totalCount.value = 0
    error.value = null
  }

  return {
    transactions,
    totalCount,
    isLoading,
    error,
    fetchTransactions,
    reset,
  }
}
