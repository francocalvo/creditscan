import { ref, computed } from 'vue'
import { OpenAPI } from '@/api'

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

  const fetchTags = async () => {
    // If we've already fetched successfully, skip the API call
    if (hasFetched.value && tags.value.length > 0) {
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const token =
        typeof OpenAPI.TOKEN === 'function' ? await OpenAPI.TOKEN({} as any) : OpenAPI.TOKEN || ''
      const url = `${OpenAPI.BASE}/api/v1/tags`

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
