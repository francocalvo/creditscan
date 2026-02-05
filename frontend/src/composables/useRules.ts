/**
 * Composable for fetching and managing rule data.
 *
 * Provides CRUD operations for rules including fetching, creating,
 * updating, deleting, toggling active status, and applying rules
 * to transactions.
 */
import { ref, computed } from 'vue'
import { RulesService } from '@/api/services.gen'
import type {
  RulePublic,
  RuleCreate,
  RuleUpdate,
  ApplyRulesRequest,
  ApplyRulesResponse,
} from '@/api/types.gen'

export type {
  RulePublic,
  RuleCreate,
  RuleUpdate,
  RuleConditionCreate,
  RuleConditionPublic,
  RuleActionCreate,
  RuleActionPublic,
  ApplyRulesRequest,
  ApplyRulesResponse,
  ConditionField,
  ConditionOperator,
  ActionType,
} from '@/api/types.gen'

export function useRules() {
  const rules = ref<RulePublic[]>([])
  const isLoading = ref(false)
  const error = ref<Error | null>(null)
  const hasFetched = ref(false)

  const rulesMap = computed<Map<string, RulePublic>>(() => {
    return new Map(rules.value.map((rule) => [rule.rule_id, rule]))
  })

  /**
   * Fetches all rules from the API.
   *
   * Uses the cache if already fetched successfully to avoid redundant API calls.
   * Sets loading state, handles errors, and updates the rules array on success.
   *
   * @param force - Force refetch even if already fetched
   */
  const fetchRules = async (force = false) => {
    if (hasFetched.value && rules.value.length > 0 && !force) {
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await RulesService.rulesListRules()
      rules.value = response.data
      hasFetched.value = true
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to fetch rules')
      console.error('Error fetching rules:', e)
      throw error.value
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Returns a rule by ID from the cache.
   *
   * @param ruleId - The ID of rule to retrieve
   * @returns The rule object if found, or undefined if not in cache
   */
  const getRuleById = (ruleId: string): RulePublic | undefined => {
    return rulesMap.value.get(ruleId)
  }

  /**
   * Creates a new rule.
   *
   * @param data - The rule data (name, conditions, actions)
   * @returns The created rule
   */
  const createRule = async (data: RuleCreate): Promise<RulePublic> => {
    error.value = null

    try {
      const createdRule = await RulesService.rulesCreateRule({ requestBody: data })
      rules.value.push(createdRule)
      return createdRule
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Failed to create rule')
      error.value = err
      console.error('Error creating rule:', e)
      throw err
    }
  }

  /**
   * Updates an existing rule.
   *
   * @param ruleId - The ID of the rule to update
   * @param data - The data to update
   * @returns The updated rule
   */
  const updateRule = async (ruleId: string, data: RuleUpdate): Promise<RulePublic> => {
    error.value = null

    try {
      const updatedRule = await RulesService.rulesUpdateRule({ ruleId, requestBody: data })
      const index = rules.value.findIndex((rule) => rule.rule_id === ruleId)
      if (index !== -1) {
        rules.value[index] = updatedRule
      }
      return updatedRule
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Failed to update rule')
      error.value = err
      console.error('Error updating rule:', e)
      throw err
    }
  }

  /**
   * Deletes a rule.
   *
   * @param ruleId - The ID of the rule to delete
   */
  const deleteRule = async (ruleId: string): Promise<void> => {
    error.value = null

    try {
      await RulesService.rulesDeleteRule({ ruleId })
      rules.value = rules.value.filter((rule) => rule.rule_id !== ruleId)
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Failed to delete rule')
      error.value = err
      console.error('Error deleting rule:', e)
      throw err
    }
  }

  /**
   * Toggles the active status of a rule.
   *
   * @param ruleId - The ID of the rule to toggle
   * @param isActive - The new active status
   * @returns The updated rule
   */
  const toggleRule = async (ruleId: string, isActive: boolean): Promise<RulePublic> => {
    return updateRule(ruleId, { is_active: isActive })
  }

  /**
   * Applies rules to transactions.
   *
   * @param params - Optional parameters to filter which transactions to apply rules to
   * @returns The result containing counts of processed transactions and applied tags
   */
  const applyRules = async (params?: ApplyRulesRequest): Promise<ApplyRulesResponse> => {
    error.value = null

    try {
      const response = await RulesService.rulesApplyRules({
        requestBody: params || {},
      })
      return response
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Failed to apply rules')
      error.value = err
      console.error('Error applying rules:', e)
      throw err
    }
  }

  return {
    rules,
    isLoading,
    error,
    hasFetched,
    fetchRules,
    getRuleById,
    createRule,
    updateRule,
    deleteRule,
    toggleRule,
    applyRules,
  }
}
