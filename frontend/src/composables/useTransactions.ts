import { ref } from 'vue'
import { TransactionsService, type Transaction } from '@/api/transactions'
import { useToast } from 'primevue/usetoast'
import { parseDateString } from '@/utils/date'
import { parseDecimal } from '@/api/currency'

export function useTransactions() {
  const transactions = ref<Transaction[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const toast = useToast()

  const fetchTransactions = async () => {
    isLoading.value = true
    error.value = null
    try {
      const response = await TransactionsService.transactionsListTransactions({
        skip: 0,
        limit: 10000,
      })
      transactions.value = response.data
    } catch (err: unknown) {
      console.error('Error fetching transactions:', err)
      error.value = err instanceof Error ? err.message : 'Failed to fetch transactions'
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load transactions',
        life: 3000,
      })
    } finally {
      isLoading.value = false
    }
  }

  const formatCurrency = (amount: number | string, currency: string = 'USD') => {
    const safeAmount = parseDecimal(amount)
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(safeAmount)
  }

  const formatDate = (dateString: string) => {
    return parseDateString(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return {
    transactions,
    isLoading,
    error,
    fetchTransactions,
    formatCurrency,
    formatDate,
  }
}
