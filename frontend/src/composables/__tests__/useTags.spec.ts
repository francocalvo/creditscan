import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useTags, type Tag } from '../useTags'

vi.mock('@/api', () => ({
  OpenAPI: {
    BASE: 'https://api.example.com',
    TOKEN: vi.fn().mockResolvedValue('test-token'),
  },
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn().mockReturnValue({
    user: { id: 'user-123' }
  })
}))

vi.mock('@/api/services.gen', () => ({
  RulesService: {
    rulesListRules: vi.fn().mockResolvedValue({
      data: [],
      count: 0
    })
  }
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

describe('useTags', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    localStorage.clear()

    // Reset shared module-level state
    const { tags, error, hasFetched } = useTags()
    tags.value = []
    error.value = null
    hasFetched.value = false
  })

  describe('createTag', () => {
    it('requires authentication (token)', async () => {
      const { OpenAPI } = await import('@/api')
      vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('')

      const { createTag } = useTags()

      await expect(
        createTag({
          label: 'Test Tag',
          color: '#EF4444'
        })
      ).rejects.toThrow('Not authenticated')

      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('requires user loaded', async () => {
      const { useAuthStore } = await import('@/stores/auth')
      vi.mocked(useAuthStore).mockReturnValueOnce({ user: null })

      const { createTag } = useTags()

      await expect(
        createTag({
          label: 'Test Tag',
          color: '#EF4444'
        })
      ).rejects.toThrow('User not loaded')
    })

    it('POSTs to /api/v1/tags/ with correct data', async () => {
      const { OpenAPI } = await import('@/api')
      vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')

      const createdTag: Tag = {
        tag_id: 'tag-123',
        user_id: 'user-123',
        label: 'Test Tag',
        color: '#EF4444',
        created_at: '2024-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => createdTag,
      })

      const { createTag, tags } = useTags()

      const input = {
        label: 'Test Tag',
        color: '#EF4444'
      }

      const result = await createTag(input)

      expect(result).toEqual(createdTag)

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/api/v1/tags/',
        expect.objectContaining({
          method: 'POST',
          headers: {
            Authorization: 'Bearer access-token',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            ...input,
            user_id: 'user-123',
          }),
        })
      )

      expect(tags.value).toContainEqual(createdTag)
    })

    it('sets error on API failure', async () => {
      const { OpenAPI } = await import('@/api')
      vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Invalid tag data' }),
      })

      const { createTag, error } = useTags()

      await expect(
        createTag({
          label: 'Test Tag',
          color: '#EF4444'
        })
      ).rejects.toThrow('Invalid tag data')

      expect(error.value?.message).toBe('Invalid tag data')
    })

    it('handles array error detail', async () => {
      const { OpenAPI } = await import('@/api')
      vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({ detail: [{ msg: 'Label is too long' }] }),
      })

      const { createTag } = useTags()

      await expect(
        createTag({
          label: 'A'.repeat(100),
          color: '#EF4444'
        })
      ).rejects.toThrow('Label is too long')
    })
  })

  describe('updateTag', () => {
    it('PATCHes to /api/v1/tags/{tagId} with correct data', async () => {
      const { OpenAPI } = await import('@/api')
      vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')

      const existingTag: Tag = {
        tag_id: 'tag-123',
        user_id: 'user-123',
        label: 'Old Label',
        color: '#EF4444',
        created_at: '2024-01-01T00:00:00Z',
      }

      const updatedTag: Tag = {
        tag_id: 'tag-123',
        user_id: 'user-123',
        label: 'New Label',
        color: '#22C55E',
        created_at: '2024-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => updatedTag,
      })

      const { updateTag, tags } = useTags()
      tags.value = [existingTag]

      const result = await updateTag('tag-123', {
        label: 'New Label',
        color: '#22C55E'
      })

      expect(result).toEqual(updatedTag)

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/api/v1/tags/tag-123',
        expect.objectContaining({
          method: 'PATCH',
          headers: {
            Authorization: 'Bearer access-token',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            label: 'New Label',
            color: '#22C55E'
          }),
        })
      )

      expect(tags.value).toEqual([updatedTag])
    })

    it('sets error on API failure', async () => {
      const { OpenAPI } = await import('@/api')
      vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Invalid update data' }),
      })

      const { updateTag, error } = useTags()

      await expect(
        updateTag('tag-123', { label: 'New Label' })
      ).rejects.toThrow('Invalid update data')

      expect(error.value?.message).toBe('Invalid update data')
    })
  })

  describe('deleteTag', () => {
    it('DELETEs from /api/v1/tags/{tagId}', async () => {
      const { OpenAPI } = await import('@/api')
      vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')

      const tagToDelete: Tag = {
        tag_id: 'tag-123',
        user_id: 'user-123',
        label: 'Delete Me',
        color: '#EF4444',
        created_at: '2024-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      })

      const { deleteTag, tags } = useTags()
      tags.value = [tagToDelete]

      await deleteTag('tag-123')

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/api/v1/tags/tag-123',
        expect.objectContaining({
          method: 'DELETE',
          headers: {
            Authorization: 'Bearer access-token',
            'Content-Type': 'application/json',
          },
        })
      )

      expect(tags.value).not.toContainEqual(tagToDelete)
    })

    it('sets error on API failure', async () => {
      const { OpenAPI } = await import('@/api')
      vi.mocked(OpenAPI.TOKEN).mockResolvedValueOnce('access-token')

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Cannot delete tag' }),
      })

      const { deleteTag, error } = useTags()

      await expect(deleteTag('tag-123')).rejects.toThrow('Cannot delete tag')

      expect(error.value?.message).toBe('Cannot delete tag')
    })
  })

  describe('getTagUsageCount', () => {
    it('returns rule count for tag', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesListRules).mockResolvedValueOnce({
        data: [
          {
            rule_id: 'rule-1',
            user_id: 'user-123',
            name: 'Rule 1',
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: null,
            conditions: [],
            actions: [
              {
                action_id: 'action-1',
                action_type: 'add_tag',
                tag_id: 'tag-123',
              },
            ],
          },
          {
            rule_id: 'rule-2',
            user_id: 'user-123',
            name: 'Rule 2',
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: null,
            conditions: [],
            actions: [
              {
                action_id: 'action-2',
                action_type: 'add_tag',
                tag_id: 'tag-456',
              },
            ],
          },
        ],
        count: 2,
      })

      const { getTagUsageCount } = useTags()

      const result = await getTagUsageCount('tag-123')

      expect(result).toEqual({
        transactions: 0,
        rules: 1,
      })

      expect(RulesService.rulesListRules).toHaveBeenCalledOnce()
    })

    it('returns zero counts on error', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesListRules).mockRejectedValueOnce(new Error('API error'))

      const { getTagUsageCount } = useTags()

      const result = await getTagUsageCount('tag-123')

      expect(result).toEqual({
        transactions: 0,
        rules: 0,
      })
    })

    it('counts multiple rules using the same tag', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesListRules).mockResolvedValueOnce({
        data: [
          {
            rule_id: 'rule-1',
            user_id: 'user-123',
            name: 'Rule 1',
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: null,
            conditions: [],
            actions: [
              {
                action_id: 'action-1',
                action_type: 'add_tag',
                tag_id: 'tag-123',
              },
            ],
          },
          {
            rule_id: 'rule-2',
            user_id: 'user-123',
            name: 'Rule 2',
            is_active: false,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: null,
            conditions: [],
            actions: [
              {
                action_id: 'action-2',
                action_type: 'add_tag',
                tag_id: 'tag-123',
              },
            ],
          },
          {
            rule_id: 'rule-3',
            user_id: 'user-123',
            name: 'Rule 3',
            is_active: true,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: null,
            conditions: [],
            actions: [
              {
                action_id: 'action-3',
                action_type: 'add_tag',
                tag_id: 'tag-456',
              },
            ],
          },
        ],
        count: 3,
      })

      const { getTagUsageCount } = useTags()

      const result = await getTagUsageCount('tag-123')

      expect(result).toEqual({
        transactions: 0,
        rules: 2,
      })
    })
  })
})
