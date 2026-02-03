import { ref, computed } from 'vue'
import type { Transaction } from '@/api/transactions'

/**
 * Date filter preset options for analytics queries.
 */
export type DateFilterPreset = 'week' | 'month' | '3months' | '6months' | 'year' | 'all'

/**
 * Summary metrics computed from filtered transactions.
 */
export interface SummaryMetrics {
    totalSpending: number
    transactionCount: number
    averageTransaction: number
    highestTransaction: number
}

/**
 * Monthly spending data for charts.
 */
export interface MonthlySpending {
    month: string
    amount: number
}

/**
 * Spending breakdown by tag/category.
 */
export interface SpendingByTag {
    tag: string
    amount: number
}

/**
 * Top merchant ranking data.
 */
export interface TopMerchant {
    payee: string
    amount: number
    count: number
    rank: number
}

/**
 * Analytics composable for financial data aggregation and visualization.
 *
 * Provides state management for transactions, date filtering, and computed metrics.
 * Includes helper functions for currency formatting and date filter management.
 *
 * @example
 * ```ts
 * const {
 *   transactions,
 *   isLoading,
 *   filteredTransactions,
 *   summaryMetrics,
 *   setDateFilter,
 *   fetchAnalytics
 * } = useAnalytics()
 * ```
 */
export function useAnalytics() {
    // State
    const transactions = ref<Transaction[]>([])
    const isLoading = ref(false)
    const error = ref<string | null>(null)
    const dateFilter = ref<DateFilterPreset>('all')
    const targetCurrency = ref('ARS')

    /**
     * Filtered transactions based on current date filter preset.
     * Placeholder implementation - returns all transactions for now.
     * Full implementation in Step 6.
     */
    const filteredTransactions = computed(() => {
        return transactions.value
    })

    /**
     * Summary metrics derived from filtered transactions.
     * Handles empty state gracefully by returning zero values.
     */
    const summaryMetrics = computed<SummaryMetrics>(() => {
        if (filteredTransactions.value.length === 0) {
            return {
                totalSpending: 0,
                transactionCount: 0,
                averageTransaction: 0,
                highestTransaction: 0,
            }
        }

        const amounts = filteredTransactions.value.map(t => t.amount)
        const totalSpending = amounts.reduce((sum, amount) => sum + amount, 0)

        return {
            totalSpending,
            transactionCount: filteredTransactions.value.length,
            averageTransaction: totalSpending / filteredTransactions.value.length,
            highestTransaction: Math.max(...amounts),
        }
    })

    /**
     * Monthly spending aggregation for charts.
     * Placeholder - returns empty array for now.
     * Full implementation in Step 10.
     */
    const spendingByMonth = computed<MonthlySpending[]>(() => {
        return []
    })

    /**
     * Spending breakdown by tag/category.
     * Placeholder - returns empty array for now.
     * Full implementation in Step 12.
     */
    const spendingByTag = computed<SpendingByTag[]>(() => {
        return []
    })

    /**
     * Top merchants ranking data.
     * Placeholder - returns empty array for now.
     * Full implementation in Step 14.
     */
    const topMerchants = computed<TopMerchant[]>(() => {
        return []
    })

    /**
     * Fetch analytics data from the backend.
     * Placeholder implementation - currently a no-op beyond state management.
     * Full implementation in Step 5.
     */
     const fetchAnalytics = async () => {
        isLoading.value = true
        error.value = null
        try {
            // TODO: Implement in Step 5 - fetch transactions with pagination
            // Currently a no-op placeholder
        } catch (err) {
            console.error('Error fetching analytics:', err)
            error.value = err instanceof Error ? err.message : 'Failed to fetch analytics data'
        } finally {
            isLoading.value = false
        }
    }

    /**
     * Set the date filter preset for analytics queries.
     *
     * @param filter - The date filter preset to apply
     */
    const setDateFilter = (filter: DateFilterPreset) => {
        dateFilter.value = filter
    }

    /**
     * Refresh analytics data by re-fetching from the backend.
     * Placeholder - calls fetchAnalytics for now.
     * Full implementation in Step 18.
     */
    const refresh = () => {
        fetchAnalytics()
    }

    /**
     * Format an amount as currency using the target currency setting.
     *
     * @param amount - The numeric amount to format
     * @returns A formatted currency string (e.g., "$1,234.56")
     *
     * @example
     * ```ts
     * formatCurrency(1234.56) // "$1,234.56" (when targetCurrency is USD)
     * ```
     */
    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: targetCurrency.value,
        }).format(amount)
    }

    return {
        // State
        transactions,
        isLoading,
        error,
        dateFilter,
        targetCurrency,

        // Computed
        filteredTransactions,
        summaryMetrics,
        spendingByMonth,
        spendingByTag,
        topMerchants,

        // Actions
        fetchAnalytics,
        setDateFilter,
        refresh,

        // Helpers
        formatCurrency,
    }
}
