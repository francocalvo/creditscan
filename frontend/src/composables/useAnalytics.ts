import { ref, computed } from 'vue'
import type { Transaction } from '@/api/transactions'
import { UsersService } from '@/api'
import { TransactionsService } from '@/api/transactions'
import { useTags } from '@/composables/useTags'
import { useTransactionTags } from '@/composables/useTransactionTags'

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
 * Spending breakdown by tag/category with percentage.
 */
export interface SpendingByTag {
    tag: string
    amount: number
    percentage: number
}

/**
 * Top merchant ranking data.
 */
export interface TopMerchant {
    payee: string
    totalAmount: number
    transactionCount: number
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

    // Tag composables
    const tags = useTags()
    const transactionTags = useTransactionTags()

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
     * Parse a date string, treating date-only format (YYYY-MM-DD) as local date.
     * Backend sends txn_date as date-only strings, which JavaScript's Date()
     * constructor parses as UTC midnight. This causes day shifts for non-UTC timezones.
     * We parse YYYY-MM-DD explicitly as local dates to avoid this issue.
     *
     * @param dateStr - The date string to parse
     * @returns A Date object for valid dates, null otherwise
     */
    const parseLocalDate = (dateStr: string): Date | null => {
        // Try YYYY-MM-DD format (date-only from backend)
        const dateOnlyMatch = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/)
        if (dateOnlyMatch) {
            const [_, yearStr, monthStr, dayStr] = dateOnlyMatch
            const year = parseInt(yearStr, 10)
            const month = parseInt(monthStr, 10) - 1  // Months are 0-indexed in JS
            const day = parseInt(dayStr, 10)
            const localDate = new Date(year, month, day)
            // Guard against overflow (e.g. 2026-02-31 becomes March 3rd in JS)
            if (
                localDate.getFullYear() !== year ||
                localDate.getMonth() !== month ||
                localDate.getDate() !== day
            ) {
                return null
            }
            return localDate
        }

        // Fallback to standard Date parsing (for full ISO datetime strings)
        const date = new Date(dateStr)
        return isNaN(date.getTime()) ? null : date
    }

    /**
     * Get the date threshold for a given filter preset.
     * Returns null for 'all' preset (no filtering), otherwise returns the
     * threshold date (inclusive) for the specified time window.
     *
     * Threshold is normalized to start-of-day (00:00:00.000) to ensure
     * consistent day-based filtering regardless of when the user applies the filter.
     *
     * The cutoff is inclusive and represents the start of the earliest day in the
     * requested window (e.g. "past 7 days" includes today + previous 6 days).
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

        // Create threshold normalized to start-of-day
        const threshold = new Date()
        threshold.setHours(0, 0, 0, 0)  // Normalize to midnight
        threshold.setDate(threshold.getDate() - (days - 1))

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
            const txnDate = parseLocalDate(txn.txn_date)
            if (!txnDate) {
                return false
            }

            // Include transactions on or after threshold date
            return txnDate >= threshold
        })
    })

    /**
     * Summary metrics derived from filtered transactions.
     * Handles empty state gracefully by returning zero values.
     *
     * Uses reduce-based max calculation to avoid argument limits on large arrays.
     * Caches transactions and computed values to avoid repeated .value accesses.
     */
    const summaryMetrics = computed<SummaryMetrics>(() => {
        const txns = filteredTransactions.value

        if (txns.length === 0) {
            return {
                totalSpending: 0,
                transactionCount: 0,
                averageTransaction: 0,
                highestTransaction: 0,
            }
        }

        // Calculate total and highest in a single reduce pass
        let total = 0
        let highest = -Infinity

        for (const txn of txns) {
            const amount = txn.amount
            total += amount
            if (amount > highest) {
                highest = amount
            }
        }

        const count = txns.length

        return {
            totalSpending: total,
            transactionCount: count,
            averageTransaction: total / count,
            highestTransaction: highest,
        }
    })

    /**
     * Monthly spending aggregation for charts.
     *
     * Groups transactions by month (YYYY-MM) and calculates total spending per month.
     * Uses parseLocalDate to handle date-only strings from backend correctly.
     * Results are sorted chronologically and month labels are formatted as "Jan 2024".
     *
     * Reactive to date filter changes through filteredTransactions dependency.
     */
    const spendingByMonth = computed<MonthlySpending[]>(() => {
        const txns = filteredTransactions.value

        if (txns.length === 0) {
            return []
        }

        // Build map keyed by YYYY-MM
        const monthlyTotals = new Map<string, number>()

        for (const txn of txns) {
            const txnDate = parseLocalDate(txn.txn_date)
            if (!txnDate) {
                continue
            }

            // Create YYYY-MM key (month is 1-indexed for sorting)
            const year = txnDate.getFullYear()
            const month = txnDate.getMonth() + 1
            const key = `${year}-${month.toString().padStart(2, '0')}`

            // Add amount to monthly total
            monthlyTotals.set(key, (monthlyTotals.get(key) || 0) + txn.amount)
        }

        // Convert map to array, sort chronologically, and format labels
        return Array.from(monthlyTotals.entries())
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([monthKey, amount]) => {
                // Parse YYYY-MM and format as "Jan 2024"
                const [year, month] = monthKey.split('-').map(Number)
                const formattedMonth = new Date(year, month - 1)
                    .toLocaleDateString('en-US', { month: 'short', year: 'numeric' })

                return {
                    month: formattedMonth,
                    amount
                }
            })
    })

    /**
     * Spending breakdown by tag/category with percentages.
     *
     * Aggregates spending by tag from filtered transactions, including an
     * "Untagged" bucket for transactions without tags. Multi-tag
     * transactions split their amount evenly across all tags.
     *
     * Each entry includes the tag name, amount, and percentage of total.
     * Results are sorted by amount descending for better visualization.
     */
    const spendingByTag = computed<SpendingByTag[]>(() => {
        const txns = filteredTransactions.value

        if (txns.length === 0) {
            return []
        }

        // Build spending by tag map
        const tagTotals = new Map<string, number>()

        for (const txn of txns) {
            // Get tag IDs for this transaction
            const tagIds = transactionTags.getTagIdsForTransaction(txn.id)

            // Use absolute amount for charting (pie slices should be non-negative)
            const effectiveAmount = Math.abs(txn.amount)

            if (tagIds.length === 0) {
                // No tags - add to "Untagged" bucket
                tagTotals.set('Untagged', (tagTotals.get('Untagged') || 0) + effectiveAmount)
            } else {
                // Split amount evenly across all tags
                const amountPerTag = effectiveAmount / tagIds.length

                for (const tagId of tagIds) {
                    // Look up tag label from cache
                    const tag = tags.getTagById(tagId)
                    const label = tag?.label || `Tag ${tagId}`

                    tagTotals.set(label, (tagTotals.get(label) || 0) + amountPerTag)
                }
            }
        }

        // Convert to array and calculate total
        const spendingEntries = Array.from(tagTotals.entries())
        const total = spendingEntries.reduce((sum, [_, amount]) => sum + amount, 0)

        // Add percentage and sort by amount descending
        return spendingEntries
            .map(([tag, amount]) => ({
                tag,
                amount,
                percentage: total > 0 ? (amount / total) * 100 : 0,
            }))
            .sort((a, b) => b.amount - a.amount)
    })

    /**
     * Top merchants ranking data.
     *
     * Aggregates spending by payee from filtered transactions and returns
     * the top 5 merchants by total amount. Transactions without a payee
     * are grouped under "Unknown".
     *
     * Reactive to date filter changes through filteredTransactions dependency.
     */
    const topMerchants = computed<TopMerchant[]>(() => {
        const txns = filteredTransactions.value

        if (txns.length === 0) {
            return []
        }

        // Build spending by payee map
        const payeeTotals = new Map<string, { totalAmount: number; transactionCount: number }>()

        for (const txn of txns) {
            // Normalize payee: use trimmed value or "Unknown" for empty/null
            const payee = txn.payee?.trim() || 'Unknown'

            // Get or create entry for this payee
            const entry = payeeTotals.get(payee) || { totalAmount: 0, transactionCount: 0 }

            // Accumulate totals
            entry.totalAmount += txn.amount
            entry.transactionCount += 1

            payeeTotals.set(payee, entry)
        }

        // Convert map to array and sort by totalAmount descending
        const sortedMerchants = Array.from(payeeTotals.entries())
            .map(([payee, data]) => ({
                payee,
                totalAmount: data.totalAmount,
                transactionCount: data.transactionCount,
            }))
            .sort((a, b) => b.totalAmount - a.totalAmount)

        // Return top 5 merchants
        return sortedMerchants.slice(0, 5)
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

            // Fetch tag data for analytics
            await tags.fetchTags() // Cached, no-op if already fetched
            transactionTags.reset() // Clear previous transaction-tag mappings

            // Fetch transaction tags in batches of ~20 for performance
            const transactionIds = allTransactions.map((txn) => txn.id)
            const batchSize = 20

            for (let i = 0; i < transactionIds.length; i += batchSize) {
                const batch = transactionIds.slice(i, i + batchSize)
                await transactionTags.fetchTagsForTransactions(batch)
            }
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
