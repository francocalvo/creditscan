import { ref } from 'vue'
import { OpenAPI } from '@/api'

export interface TransactionTagMapping {
  transaction_id: string
  tag_id: string
}

export function useTransactionTags() {
  const tagsByTransaction = ref<Map<string, string[]>>(new Map())
  const isLoading = ref(false)

  const fetchTagsForTransactions = async (transactionIds: string[]): Promise<void> => {
    // Early return if no transaction IDs to fetch
    if (transactionIds.length === 0) {
      return
    }

    isLoading.value = true

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function' ? await OpenAPI.TOKEN({} as any) : OpenAPI.TOKEN || ''

      // Create fetch promises for each transaction ID
      // Each promise returns both the transaction ID and the response for proper mapping
      const fetchPromises = transactionIds.map(async (txnId) => {
        const url = `${OpenAPI.BASE}/api/v1/transaction-tags/transaction/${txnId}`

        try {
          const response = await fetch(url, {
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          })

          return { txnId, response }
        } catch (error) {
          // Return the transaction ID with a failed response object
          return {
            txnId,
            response: null,
            error: error instanceof Error ? error : new Error('Failed to fetch transaction tags'),
          }
        }
      })

      // Execute all fetches in parallel
      const results = await Promise.allSettled(fetchPromises)

      // Process results: store tag IDs for successful fetches, empty array for failures
      for (const result of results) {
        if (result.status === 'fulfilled') {
          const { txnId, response, error } = result.value

          // Check for error from fetch itself
          if (error || response === null) {
            tagsByTransaction.value.set(txnId, [])
            continue
          }

          // Check for HTTP error response
          if (response.ok) {
            try {
              const data: TransactionTagMapping[] = await response.json()
              const tagIds = data.map((mapping) => mapping.tag_id)
              tagsByTransaction.value.set(txnId, tagIds)
            } catch {
              // Failed to parse response - store empty array (graceful failure)
              tagsByTransaction.value.set(txnId, [])
            }
          } else {
            // Non-ok response - store empty array (graceful failure)
            tagsByTransaction.value.set(txnId, [])
          }
        } else {
          // Promise rejected - store empty array (graceful failure)
          // We can't get the transaction ID from a rejected promise without additional tracking
          // This is acceptable as the transaction won't be displayed with tags
        }
      }
    } finally {
      isLoading.value = false
    }
  }

  const getTagIdsForTransaction = (transactionId: string): string[] => {
    return tagsByTransaction.value.get(transactionId) || []
  }

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
