import { ref, computed } from 'vue'
import type { Transaction } from '@/api/transactions'
import { UsersService } from '@/api'
import { TransactionsService } from '@/api/transactions'

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
     * Validates that a string is a valid ISO 4217 currency code.
     * Uses Intl.NumberFormat to test if the currency code is recognized.
     *
     * @param currency - The currency code to validate
     * @returns True if the currency code is valid, false otherwise
     */
    const isValidCurrency = (currency: string): boolean => {
        try {
            new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(0)
            return true
        } catch {
            return false
        }
    }

    /**
     * Get the date threshold for a given filter preset.
     * Returns null for 'all' preset (no filtering), otherwise returns the
     * threshold date (inclusive) for the specified time window.
     *
     * @param preset - The date filter preset to get threshold for
     * @returns The threshold Date object, or null for 'all' preset
     */
    const getDateThreshold = (preset: DateFilterPreset): Date | null => {
        // 'all' preset means no filtering
        if (preset === 'all') {
            return null
        }

        // Calculate days to subtract based on preset
        const daysMap: Record<Exclude<DateFilterPreset, 'all'>, number> = {
            week: 7,
            month: 30,
            '3months': 90,
            '6months': 180,
            year: 365,
        }

        const days = daysMap[preset as Exclude<DateFilterPreset, 'all'>]
        const threshold = new Date()
        threshold.setDate(threshold.getDate() - days)

        return threshold
    }

    /**
     * Filtered transactions based on current date filter preset.
     *
     * Uses the getDateThreshold helper to calculate the cutoff date.
     * Transactions with invalid txn_date values are excluded from results.
     *
     * Filtering is inclusive: transactions on or after the threshold are included.
     */
    const filteredTransactions = computed(() => {
        const threshold = getDateThreshold(dateFilter.value)

        // 'all' preset: return all transactions as-is (preserves stable references)
        if (threshold === null) {
            return transactions.value
        }

        // Filter transactions by date, excluding invalid txn_date values
        return transactions.value.filter((txn) => {
            const txnDate = new Date(txn.txn_date)

            // Exclude transactions with invalid dates
            if (isNaN(txnDate.getTime())) {
                return false
            }

            // Include transactions on or after threshold date
            return txnDate >= threshold
        })
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
     * Implements paginated transaction fetching and user preference loading.
     */
    const fetchAnalytics = async () => {
        isLoading.value = true
        error.value = null
        try {
            // Fetch current user and set target currency from preferences
            const userResponse = await UsersService.readUserMe()
            const user = userResponse as UserPublicWithCurrency

            // Validate and set target currency, falling back to 'ARS' if invalid
            const currencyFromProfile = user.preferred_currency ?? 'ARS'
            targetCurrency.value = isValidCurrency(currencyFromProfile)
                ? currencyFromProfile
                : 'ARS'

            // Fetch all transactions with pagination
            const allTransactions: Transaction[] = []
            const limit = 100
            let skip = 0
            let totalCount: number | null = null

            while (true) {
                const response = await TransactionsService.listTransactions(skip, limit)
                const { data, count } = response

                // Update total count from first response (null sentinel)
                if (totalCount === null) {
                    totalCount = count
                }

                // Add transactions to accumulator
                allTransactions.push(...data)

                // Termination conditions:
                // 1. We've fetched all known transactions (accumulated length == total count)
                // 2. Empty page returned (safety guard)
                // 3. Null total count with empty response (edge case)
                if ((totalCount !== null && allTransactions.length >= totalCount) || data.length === 0) {
                    break
                }

                // Prepare for next page
                skip += limit
            }

            // Assign transactions once after loop completes
            transactions.value = allTransactions
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
        return fetchAnalytics()
    }

    /**
     * Format an amount as currency using the target currency setting.
     * Falls back to USD if target currency is invalid.
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
        const currency = isValidCurrency(targetCurrency.value)
            ? targetCurrency.value
            : 'USD'

        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency,
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
