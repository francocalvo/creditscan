import { ref } from 'vue'
import { TransactionsService, type Transaction } from '@/api/transactions'
import { useToast } from 'primevue/usetoast'

export function useTransactions() {
    const transactions = ref<Transaction[]>([])
    const isLoading = ref(false)
    const error = ref<string | null>(null)
    const toast = useToast()

    const fetchTransactions = async () => {
        isLoading.value = true
        error.value = null
        try {
            const response = await TransactionsService.listTransactions()
            // Sort by date descending (newest first)
            transactions.value = response.data.sort((a, b) => {
                return new Date(b.txn_date).getTime() - new Date(a.txn_date).getTime()
            })
        } catch (err: any) {
            console.error('Error fetching transactions:', err)
            error.value = err.message || 'Failed to fetch transactions'
            toast.add({
                severity: 'error',
                summary: 'Error',
                detail: 'Failed to load transactions',
                life: 3000
            })
        } finally {
            isLoading.value = false
        }
    }

    const formatCurrency = (amount: number, currency: string = 'USD') => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount)
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        })
    }

    return {
        transactions,
        isLoading,
        error,
        fetchTransactions,
        formatCurrency,
        formatDate
    }
}
