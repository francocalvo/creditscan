/**
 * Composable for fetching tag mappings for transactions.
 *
 * Fetches tag IDs for multiple transactions in a single batch request.
 * Uses the POST /api/v1/transaction-tags/batch endpoint to avoid
 * making one request per transaction.
 */
import { ref } from 'vue'
import { OpenAPI } from '@/api'
import type { ApiRequestOptions } from '@/api/core/ApiRequestOptions'

export interface TransactionTagMapping {
  transaction_id: string
  tag_id: string
}

export function useTransactionTags() {
  const tagsByTransaction = ref<Map<string, string[]>>(new Map())
  const isLoading = ref(false)

  /**
   * Fetches tag IDs for multiple transactions in a single batch request.
   *
   * @param transactionIds - Array of transaction IDs to fetch tags for
   */
  const fetchTagsForTransactions = async (transactionIds: string[]): Promise<void> => {
    if (transactionIds.length === 0) {
      return
    }

    isLoading.value = true

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'POST',
              url: '/api/v1/transaction-tags/batch',
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''

      const url = `${OpenAPI.BASE}/api/v1/transaction-tags/batch`

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ transaction_ids: transactionIds }),
      })

      if (!response.ok) {
        console.error('Failed to fetch transaction tags:', response.statusText)
        return
      }

      const data: TransactionTagMapping[] = await response.json()

      // Initialize all requested transactions with empty arrays
      for (const txnId of transactionIds) {
        tagsByTransaction.value.set(txnId, [])
      }

      // Group tag IDs by transaction
      for (const mapping of data) {
        const existing = tagsByTransaction.value.get(mapping.transaction_id) || []
        existing.push(mapping.tag_id)
        tagsByTransaction.value.set(mapping.transaction_id, existing)
      }
    } catch (error) {
      console.error('Error fetching transaction tags:', error)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Returns tag IDs for a specific transaction.
   *
   * @param transactionId - The ID of the transaction to get tags for
   * @returns Array of tag IDs, or empty array if none found or not yet fetched
   */
  const getTagIdsForTransaction = (transactionId: string): string[] => {
    return tagsByTransaction.value.get(transactionId) || []
  }

  /**
   * Clears all tag mappings from the cache.
   */
  const reset = (): void => {
    tagsByTransaction.value = new Map()
  }

  return {
    tagsByTransaction,
    isLoading,
    fetchTagsForTransactions,
    getTagIdsForTransaction,
    reset,
  }
}
