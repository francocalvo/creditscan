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

export interface Tag {
  tag_id: string
  user_id: string
  label: string
  created_at: string
}

export interface TagsResponse {
  data: Tag[]
  count: number
}

export function useTags() {
  const tags = ref<Tag[]>([])
  const isLoading = ref(false)
  const error = ref<Error | null>(null)
  const hasFetched = ref(false)

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
   * @param tagId - The ID of the tag to retrieve
   * @returns The tag object if found, or undefined if not in cache
   */
  const getTagById = (tagId: string): Tag | undefined => {
    return tagsMap.value.get(tagId)
  }

  return {
    tags,
    isLoading,
    error,
    hasFetched,
    fetchTags,
    getTagById,
  }
}
