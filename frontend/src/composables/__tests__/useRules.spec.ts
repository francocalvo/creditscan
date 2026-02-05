import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useRules } from '../useRules'
import type { RulePublic, ApplyRulesResponse } from '@/api/types.gen'

vi.mock('@/api/services.gen', () => ({
  RulesService: {
    rulesListRules: vi.fn(),
    rulesCreateRule: vi.fn(),
    rulesUpdateRule: vi.fn(),
    rulesDeleteRule: vi.fn(),
    rulesApplyRules: vi.fn(),
  },
}))

const createMockRule = (overrides: Partial<RulePublic> = {}): RulePublic => ({
  rule_id: 'rule-123',
  user_id: 'user-123',
  name: 'Test Rule',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
  conditions: [
    {
      condition_id: 'condition-1',
      field: 'payee',
      operator: 'contains',
      value: 'Amazon',
    },
  ],
  actions: [
    {
      action_id: 'action-1',
      action_type: 'add_tag',
      tag_id: 'tag-123',
    },
  ],
  ...overrides,
})

describe('useRules', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchRules', () => {
    it('retrieves rules from API and stores them', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const mockRules = [
        createMockRule({ rule_id: 'rule-1', name: 'Rule 1' }),
        createMockRule({ rule_id: 'rule-2', name: 'Rule 2' }),
      ]

      vi.mocked(RulesService.rulesListRules).mockResolvedValueOnce({
        data: mockRules,
      })

      const { rules, fetchRules, hasFetched, isLoading } = useRules()

      expect(rules.value).toEqual([])
      expect(hasFetched.value).toBe(false)

      await fetchRules()

      expect(RulesService.rulesListRules).toHaveBeenCalledOnce()
      expect(rules.value).toEqual(mockRules)
      expect(hasFetched.value).toBe(true)
      expect(isLoading.value).toBe(false)
    })

    it('uses cache when already fetched', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const mockRules = [createMockRule()]

      vi.mocked(RulesService.rulesListRules).mockResolvedValueOnce({
        data: mockRules,
      })

      const { fetchRules } = useRules()

      await fetchRules()
      await fetchRules()

      expect(RulesService.rulesListRules).toHaveBeenCalledOnce()
    })

    it('force fetches when force parameter is true', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const mockRules = [createMockRule()]

      vi.mocked(RulesService.rulesListRules).mockResolvedValue({
        data: mockRules,
      })

      const { fetchRules } = useRules()

      await fetchRules()
      await fetchRules(true)

      expect(RulesService.rulesListRules).toHaveBeenCalledTimes(2)
    })

    it('sets error on API failure', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesListRules).mockRejectedValueOnce(
        new Error('Network error')
      )

      const { fetchRules, error, isLoading } = useRules()

      await expect(fetchRules()).rejects.toThrow('Network error')

      expect(error.value?.message).toBe('Network error')
      expect(isLoading.value).toBe(false)
    })

    it('wraps non-Error throws in Error', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesListRules).mockRejectedValueOnce('String error')

      const { fetchRules, error } = useRules()

      await expect(fetchRules()).rejects.toThrow('Failed to fetch rules')

      expect(error.value?.message).toBe('Failed to fetch rules')
    })

    it('sets isLoading during fetch', async () => {
      const { RulesService } = await import('@/api/services.gen')
      let resolvePromise: (value: { data: RulePublic[] }) => void
      const pendingPromise = new Promise<{ data: RulePublic[] }>((resolve) => {
        resolvePromise = resolve
      })

      vi.mocked(RulesService.rulesListRules).mockReturnValueOnce(pendingPromise)

      const { fetchRules, isLoading } = useRules()

      expect(isLoading.value).toBe(false)

      const fetchPromise = fetchRules()
      expect(isLoading.value).toBe(true)

      resolvePromise!({ data: [] })
      await fetchPromise

      expect(isLoading.value).toBe(false)
    })
  })

  describe('createRule', () => {
    it('creates a new rule and adds it to the array', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const newRule = createMockRule({ rule_id: 'new-rule', name: 'New Rule' })

      vi.mocked(RulesService.rulesCreateRule).mockResolvedValueOnce(newRule)

      const { rules, createRule } = useRules()

      const result = await createRule({
        name: 'New Rule',
        conditions: [
          { field: 'payee', operator: 'contains', value: 'Amazon' },
        ],
        actions: [{ action_type: 'add_tag', tag_id: 'tag-123' }],
      })

      expect(RulesService.rulesCreateRule).toHaveBeenCalledWith({
        requestBody: {
          name: 'New Rule',
          conditions: [
            { field: 'payee', operator: 'contains', value: 'Amazon' },
          ],
          actions: [{ action_type: 'add_tag', tag_id: 'tag-123' }],
        },
      })

      expect(result).toEqual(newRule)
      expect(rules.value).toContainEqual(newRule)
    })

    it('sets error on API failure', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesCreateRule).mockRejectedValueOnce(
        new Error('Validation error')
      )

      const { createRule, error } = useRules()

      await expect(
        createRule({
          name: 'Test',
          conditions: [],
          actions: [],
        })
      ).rejects.toThrow('Validation error')

      expect(error.value?.message).toBe('Validation error')
    })
  })

  describe('updateRule', () => {
    it('updates an existing rule and updates it in the array', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const existingRule = createMockRule({
        rule_id: 'rule-1',
        name: 'Old Name',
      })
      const updatedRule = createMockRule({
        rule_id: 'rule-1',
        name: 'New Name',
      })

      vi.mocked(RulesService.rulesUpdateRule).mockResolvedValueOnce(updatedRule)

      const { rules, updateRule } = useRules()
      rules.value = [existingRule]

      const result = await updateRule('rule-1', { name: 'New Name' })

      expect(RulesService.rulesUpdateRule).toHaveBeenCalledWith({
        ruleId: 'rule-1',
        requestBody: { name: 'New Name' },
      })

      expect(result).toEqual(updatedRule)
      expect(rules.value).toEqual([updatedRule])
    })

    it('handles update for rule not in local array', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const updatedRule = createMockRule({
        rule_id: 'rule-1',
        name: 'New Name',
      })

      vi.mocked(RulesService.rulesUpdateRule).mockResolvedValueOnce(updatedRule)

      const { rules, updateRule } = useRules()

      const result = await updateRule('rule-1', { name: 'New Name' })

      expect(result).toEqual(updatedRule)
      expect(rules.value).toEqual([])
    })

    it('sets error on API failure', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesUpdateRule).mockRejectedValueOnce(
        new Error('Not found')
      )

      const { updateRule, error } = useRules()

      await expect(updateRule('rule-1', { name: 'Test' })).rejects.toThrow(
        'Not found'
      )

      expect(error.value?.message).toBe('Not found')
    })
  })

  describe('deleteRule', () => {
    it('deletes a rule and removes it from the array', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const ruleToDelete = createMockRule({ rule_id: 'rule-1' })
      const otherRule = createMockRule({ rule_id: 'rule-2' })

      vi.mocked(RulesService.rulesDeleteRule).mockResolvedValueOnce(undefined)

      const { rules, deleteRule } = useRules()
      rules.value = [ruleToDelete, otherRule]

      await deleteRule('rule-1')

      expect(RulesService.rulesDeleteRule).toHaveBeenCalledWith({
        ruleId: 'rule-1',
      })

      expect(rules.value).toEqual([otherRule])
    })

    it('sets error on API failure', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesDeleteRule).mockRejectedValueOnce(
        new Error('Delete failed')
      )

      const { deleteRule, error } = useRules()

      await expect(deleteRule('rule-1')).rejects.toThrow('Delete failed')

      expect(error.value?.message).toBe('Delete failed')
    })
  })

  describe('toggleRule', () => {
    it('changes active status using updateRule', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const rule = createMockRule({ rule_id: 'rule-1', is_active: true })
      const toggledRule = createMockRule({
        rule_id: 'rule-1',
        is_active: false,
      })

      vi.mocked(RulesService.rulesUpdateRule).mockResolvedValueOnce(toggledRule)

      const { rules, toggleRule } = useRules()
      rules.value = [rule]

      const result = await toggleRule('rule-1', false)

      expect(RulesService.rulesUpdateRule).toHaveBeenCalledWith({
        ruleId: 'rule-1',
        requestBody: { is_active: false },
      })

      expect(result).toEqual(toggledRule)
      expect(rules.value[0].is_active).toBe(false)
    })

    it('can toggle from inactive to active', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const rule = createMockRule({ rule_id: 'rule-1', is_active: false })
      const toggledRule = createMockRule({
        rule_id: 'rule-1',
        is_active: true,
      })

      vi.mocked(RulesService.rulesUpdateRule).mockResolvedValueOnce(toggledRule)

      const { rules, toggleRule } = useRules()
      rules.value = [rule]

      const result = await toggleRule('rule-1', true)

      expect(result.is_active).toBe(true)
    })
  })

  describe('applyRules', () => {
    it('triggers rule execution and returns results', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const applyResult: ApplyRulesResponse = {
        transactions_processed: 50,
        tags_applied: 12,
      }

      vi.mocked(RulesService.rulesApplyRules).mockResolvedValueOnce(applyResult)

      const { applyRules } = useRules()

      const result = await applyRules()

      expect(RulesService.rulesApplyRules).toHaveBeenCalledWith({
        requestBody: {},
      })

      expect(result).toEqual(applyResult)
    })

    it('passes optional parameters', async () => {
      const { RulesService } = await import('@/api/services.gen')
      const applyResult: ApplyRulesResponse = {
        transactions_processed: 10,
        tags_applied: 3,
      }

      vi.mocked(RulesService.rulesApplyRules).mockResolvedValueOnce(applyResult)

      const { applyRules } = useRules()

      const result = await applyRules({ statement_id: 'stmt-123' })

      expect(RulesService.rulesApplyRules).toHaveBeenCalledWith({
        requestBody: { statement_id: 'stmt-123' },
      })

      expect(result).toEqual(applyResult)
    })

    it('sets error on API failure', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesApplyRules).mockRejectedValueOnce(
        new Error('Apply failed')
      )

      const { applyRules, error } = useRules()

      await expect(applyRules()).rejects.toThrow('Apply failed')

      expect(error.value?.message).toBe('Apply failed')
    })
  })

  describe('getRuleById', () => {
    it('returns rule from cache by ID', () => {
      const rule1 = createMockRule({ rule_id: 'rule-1', name: 'Rule 1' })
      const rule2 = createMockRule({ rule_id: 'rule-2', name: 'Rule 2' })

      const { rules, getRuleById } = useRules()
      rules.value = [rule1, rule2]

      expect(getRuleById('rule-1')).toEqual(rule1)
      expect(getRuleById('rule-2')).toEqual(rule2)
    })

    it('returns undefined for non-existent ID', () => {
      const { getRuleById } = useRules()

      expect(getRuleById('non-existent')).toBeUndefined()
    })
  })

  describe('error and loading state management', () => {
    it('clears error before new operations', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesListRules).mockRejectedValueOnce(
        new Error('First error')
      )
      vi.mocked(RulesService.rulesListRules).mockResolvedValueOnce({ data: [] })

      const { fetchRules, error } = useRules()

      await expect(fetchRules()).rejects.toThrow()
      expect(error.value?.message).toBe('First error')

      await fetchRules(true)
      expect(error.value).toBeNull()
    })

    it('isLoading is false after error', async () => {
      const { RulesService } = await import('@/api/services.gen')
      vi.mocked(RulesService.rulesListRules).mockRejectedValueOnce(new Error('Error'))

      const { fetchRules, isLoading } = useRules()

      await expect(fetchRules()).rejects.toThrow()

      expect(isLoading.value).toBe(false)
    })
  })
})
