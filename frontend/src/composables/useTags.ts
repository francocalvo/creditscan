/**
 * Composable for fetching and caching tag data.
 *
 * Fetches all tags from the API once and caches them locally.
 * Subsequent calls to fetchTags() will use the cache instead of making
 * additional API requests. Provides a fast lookup method to retrieve
 * tags by ID from the cached data.
 */
import { ref, computed } from 'vue'
import { OpenAPI } from '@/api'
import type { ApiRequestOptions } from '@/api/core/ApiRequestOptions'
import { RulesService } from '@/api/services.gen'
import { useAuthStore } from '@/stores/auth'

export interface Tag {
  tag_id: string
  user_id: string
  label: string
  color?: string | null
  created_at: string
}

export interface TagsResponse {
  data: Tag[]
  count: number
}

// Module-level shared state (singleton across all consumers)
const tags = ref<Tag[]>([])
const isLoading = ref(false)
const error = ref<Error | null>(null)
const hasFetched = ref(false)

export function useTags() {

  const tagsMap = computed<Map<string, Tag>>(() => {
    return new Map(tags.value.map((tag) => [tag.tag_id, tag]))
  })

  /**
   * Fetches all tags from the API.
   *
   * Uses the cache if already fetched successfully to avoid redundant API calls.
   * Sets loading state, handles errors, and updates the tags array on success.
   */
  const fetchTags = async () => {
    // If we've already fetched successfully, skip the API call
    if (hasFetched.value && tags.value.length > 0) {
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function'
          ? await OpenAPI.TOKEN({
              method: 'GET',
              url: '/api/v1/tags/',
            } as ApiRequestOptions<string>)
          : OpenAPI.TOKEN || ''
      const url = `${OpenAPI.BASE}/api/v1/tags/`

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch tags: ${response.statusText}`)
      }

      const data: TagsResponse = await response.json()
      tags.value = data.data
      hasFetched.value = true
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to fetch tags')
      console.error('Error fetching tags:', e)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Returns a tag by ID from the cache.
   *
   * @param tagId - The ID of tag to retrieve
   * @returns The tag object if found, or undefined if not in cache
   */
  const getTagById = (tagId: string): Tag | undefined => {
    return tagsMap.value.get(tagId)
  }

  /**
   * Creates a new tag for the current user.
   *
   * @param data - The tag data (label and optional color)
   * @returns The created tag
   */
  const createTag = async (data: { label: string; color?: string | null }): Promise<Tag> => {
    error.value = null

    const authStore = useAuthStore()
    if (!authStore.user?.id) {
      const authError = new Error('User not loaded')
      error.value = authError
      throw authError
    }

    const token =
      typeof OpenAPI.TOKEN === 'function'
        ? await OpenAPI.TOKEN({
            method: 'POST',
            url: '/api/v1/tags/',
          } as ApiRequestOptions<string>)
        : OpenAPI.TOKEN || ''

    if (!token) {
      const authError = new Error('Not authenticated')
      error.value = authError
      throw authError
    }

    const url = `${OpenAPI.BASE}/api/v1/tags/`

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...data,
          user_id: authStore.user.id,
        }),
      })

      if (!response.ok) {
        let message = 'Failed to create tag'
        try {
          const body: unknown = await response.json()
          if (typeof body === 'object' && body !== null && 'detail' in body) {
            const detail = (body as { detail?: unknown }).detail
            if (typeof detail === 'string' && detail.trim()) {
              message = detail
            } else if (Array.isArray(detail)) {
              const firstMessage = detail
                .map((item) => {
                  if (typeof item === 'string') return item
                  if (typeof item === 'object' && item !== null && 'msg' in item) {
                    const msg = (item as { msg?: unknown }).msg
                    return typeof msg === 'string' ? msg : ''
                  }
                  return ''
                })
                .find((msg) => msg.trim())
              if (firstMessage) message = firstMessage
            }
          }
        } catch {
          // ignore JSON parsing errors and fall back to default message
        }

        throw new Error(message)
      }

      const createdTag: Tag = await response.json()
      // Optimistically update the tags array
      tags.value.push(createdTag)
      return createdTag
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Failed to create tag')
      error.value = err
      throw err
    }
  }

  /**
   * Updates an existing tag.
   *
   * @param tagId - The ID of the tag to update
   * @param data - The data to update (label and/or color)
   * @returns The updated tag
   */
  const updateTag = async (tagId: string, data: { label?: string; color?: string | null }): Promise<Tag> => {
    error.value = null

    const token =
      typeof OpenAPI.TOKEN === 'function'
        ? await OpenAPI.TOKEN({
            method: 'PATCH',
            url: `/api/v1/tags/${tagId}`,
          } as ApiRequestOptions<string>)
        : OpenAPI.TOKEN || ''

    if (!token) {
      const authError = new Error('Not authenticated')
      error.value = authError
      throw authError
    }

    const url = `${OpenAPI.BASE}/api/v1/tags/${tagId}`

    try {
      const response = await fetch(url, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        let message = 'Failed to update tag'
        try {
          const body: unknown = await response.json()
          if (typeof body === 'object' && body !== null && 'detail' in body) {
            const detail = (body as { detail?: unknown }).detail
            if (typeof detail === 'string' && detail.trim()) {
              message = detail
            } else if (Array.isArray(detail)) {
              const firstMessage = detail
                .map((item) => {
                  if (typeof item === 'string') return item
                  if (typeof item === 'object' && item !== null && 'msg' in item) {
                    const msg = (item as { msg?: unknown }).msg
                    return typeof msg === 'string' ? msg : ''
                  }
                  return ''
                })
                .find((msg) => msg.trim())
              if (firstMessage) message = firstMessage
            }
          }
        } catch {
          // ignore JSON parsing errors and fall back to default message
        }

        throw new Error(message)
      }

      const updatedTag: Tag = await response.json()
      // Optimistically update the tag in the array
      const index = tags.value.findIndex((tag) => tag.tag_id === tagId)
      if (index !== -1) {
        tags.value[index] = updatedTag
      }
      return updatedTag
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Failed to update tag')
      error.value = err
      throw err
    }
  }

  /**
   * Deletes a tag.
   *
   * @param tagId - The ID of the tag to delete
   */
  const deleteTag = async (tagId: string): Promise<void> => {
    error.value = null

    const token =
      typeof OpenAPI.TOKEN === 'function'
        ? await OpenAPI.TOKEN({
            method: 'DELETE',
            url: `/api/v1/tags/${tagId}`,
          } as ApiRequestOptions<string>)
        : OpenAPI.TOKEN || ''

    if (!token) {
      const authError = new Error('Not authenticated')
      error.value = authError
      throw authError
    }

    const url = `${OpenAPI.BASE}/api/v1/tags/${tagId}`

    try {
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        let message = 'Failed to delete tag'
        try {
          const body: unknown = await response.json()
          if (typeof body === 'object' && body !== null && 'detail' in body) {
            const detail = (body as { detail?: unknown }).detail
            if (typeof detail === 'string' && detail.trim()) {
              message = detail
            } else if (Array.isArray(detail)) {
              const firstMessage = detail
                .map((item) => {
                  if (typeof item === 'string') return item
                  if (typeof item === 'object' && item !== null && 'msg' in item) {
                    const msg = (item as { msg?: unknown }).msg
                    return typeof msg === 'string' ? msg : ''
                  }
                  return ''
                })
                .find((msg) => msg.trim())
              if (firstMessage) message = firstMessage
            }
          }
        } catch {
          // ignore JSON parsing errors and fall back to default message
        }

        throw new Error(message)
      }

      // Optimistically remove the tag from the array
      tags.value = tags.value.filter((tag) => tag.tag_id !== tagId)
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Failed to delete tag')
      error.value = err
      throw err
    }
  }

  /**
   * Gets the usage count for a tag.
   *
   * Returns the number of rules and transactions that reference this tag.
   * Note: Transaction count is currently 0 as there's no backend endpoint to count efficiently.
   *
   * @param tagId - The ID of the tag to check usage for
   * @returns Object with transactions and rules counts
   */
  const getTagUsageCount = async (tagId: string): Promise<{ transactions: number; rules: number }> => {
    try {
      // Fetch all rules to count how many use this tag
      const rules = await RulesService.rulesListRules()

      // Count rules where any action references the tag
      const ruleCount = rules.data.filter((rule) =>
        rule.actions.some((action) => action.tag_id === tagId),
      ).length

      // Transaction count requires backend support - returning 0 for now
      // Full implementation would need an endpoint like GET /api/v1/transaction-tags/count?tag_id={tagId}
      return {
        transactions: 0,
        rules: ruleCount,
      }
    } catch (e) {
      console.error('Error fetching tag usage count:', e)
      // Return 0 counts on error rather than throwing
      return {
        transactions: 0,
        rules: 0,
      }
    }
  }

  return {
    tags,
    isLoading,
    error,
    hasFetched,
    fetchTags,
    getTagById,
    createTag,
    updateTag,
    deleteTag,
    getTagUsageCount,
  }
}
