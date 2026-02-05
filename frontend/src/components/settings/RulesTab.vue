<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRules, type RulePublic, type RuleConditionPublic } from '@/composables/useRules'
import { useTags, type Tag } from '@/composables/useTags'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import InputSwitch from 'primevue/inputswitch'
import RuleFormModal from './RuleFormModal.vue'
import DeleteConfirmDialog from './DeleteConfirmDialog.vue'

const toast = useToast()
const { rules, isLoading, fetchRules, toggleRule, applyRules, deleteRule } = useRules()
const { tags, fetchTags } = useTags()

// State for modal interactions (handlers ready for Steps 11-12)
const showCreateModal = ref(false)
const editingRule = ref<RulePublic | null>(null)
const deletingRule = ref<RulePublic | null>(null)
const showDeleteDialog = ref(false)
const isDeleting = ref(false)

/**
 * Computed for modal visibility (combines create and edit modes)
 */
const showRuleModal = computed(() => showCreateModal.value || editingRule.value !== null)

// Apply rules state
const isApplying = ref(false)

// Track toggle loading state per rule
const togglingRules = ref<Set<string>>(new Set())

onMounted(() => {
  fetchRules()
  fetchTags()
})

/**
 * Build a map of tag_id -> Tag for quick lookup
 */
const tagsMap = computed<Map<string, Tag>>(() => {
  return new Map(tags.value.map((tag) => [tag.tag_id, tag]))
})

/**
 * Get the tag for a rule's first action
 */
function getTagForRule(rule: RulePublic): Tag | undefined {
  const firstAction = rule.actions[0]
  if (!firstAction) return undefined
  return tagsMap.value.get(firstAction.tag_id)
}

/**
 * Format a single condition for display
 */
function formatCondition(condition: RuleConditionPublic): string {
  const fieldLabels: Record<string, string> = {
    payee: 'Payee',
    description: 'Description',
    amount: 'Amount',
    date: 'Date',
  }

  const operatorLabels: Record<string, string> = {
    contains: 'contains',
    equals: 'equals',
    gt: '>',
    lt: '<',
    before: 'before',
    after: 'after',
    between: 'between',
  }

  const field = fieldLabels[condition.field] || condition.field
  const operator = operatorLabels[condition.operator] || condition.operator

  if (condition.operator === 'between' && condition.value_secondary) {
    return `${field} ${operator} ${condition.value} and ${condition.value_secondary}`
  }

  return `${field} ${operator} "${condition.value}"`
}

/**
 * Format all conditions for a rule as a summary string
 */
function formatConditions(rule: RulePublic): string {
  if (rule.conditions.length === 0) return 'No conditions'

  // Sort by position and join with logical operator
  const sortedConditions = [...rule.conditions].sort((a, b) => a.position - b.position)

  return sortedConditions.map((c, i) => {
    const formatted = formatCondition(c)
    if (i === 0) return formatted
    return `${c.logical_operator} ${formatted}`
  }).join(' ')
}

/**
 * Handle create rule button
 */
function handleCreate(): void {
  showCreateModal.value = true
}

/**
 * Handle edit rule button
 */
function handleEdit(rule: RulePublic): void {
  editingRule.value = rule
}

/**
 * Handle delete rule button
 */
function handleDelete(rule: RulePublic): void {
  deletingRule.value = rule
  showDeleteDialog.value = true
}

/**
 * Handle delete confirmation
 */
async function confirmDelete(): Promise<void> {
  if (!deletingRule.value) return

  isDeleting.value = true

  try {
    await deleteRule(deletingRule.value.rule_id)

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `Rule "${deletingRule.value.name}" deleted`,
      life: 3000,
    })

    showDeleteDialog.value = false
    deletingRule.value = null
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: e instanceof Error ? e.message : 'Failed to delete rule',
      life: 5000,
    })
  } finally {
    isDeleting.value = false
  }
}

/**
 * Handle delete dialog cancel
 */
function handleDeleteCancel(): void {
  showDeleteDialog.value = false
  deletingRule.value = null
}

/**
 * Handle toggle rule active state
 */
async function handleToggle(rule: RulePublic, isActive: boolean): Promise<void> {
  togglingRules.value.add(rule.rule_id)

  try {
    await toggleRule(rule.rule_id, isActive)
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: e instanceof Error ? e.message : 'Failed to update rule',
      life: 5000,
    })
    // Revert the toggle in the UI by refetching
    await fetchRules(true)
  } finally {
    togglingRules.value.delete(rule.rule_id)
  }
}

/**
 * Handle apply rules button
 */
async function handleApplyRules(): Promise<void> {
  isApplying.value = true

  try {
    const result = await applyRules({})

    toast.add({
      severity: 'success',
      summary: 'Rules Applied',
      detail: `Processed ${result.transactions_processed} transactions, applied ${result.tags_applied} tags`,
      life: 5000,
    })
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: e instanceof Error ? e.message : 'Failed to apply rules',
      life: 5000,
    })
  } finally {
    isApplying.value = false
  }
}

/**
 * Handle modal close
 */
function handleModalClose(visible: boolean): void {
  if (!visible) {
    showCreateModal.value = false
    editingRule.value = null
  }
}

/**
 * Handle rule saved (create or update)
 */
async function handleRuleSaved(): Promise<void> {
  const wasEditing = editingRule.value !== null
  showCreateModal.value = false
  editingRule.value = null
  await fetchRules(true)
  toast.add({
    severity: 'success',
    summary: 'Success',
    detail: wasEditing ? 'Rule updated' : 'Rule created',
    life: 3000,
  })
}
</script>

<template>
  <div class="rules-tab">
    <!-- Header -->
    <div class="tab-header">
      <h3 class="tab-title">Rules</h3>
      <div class="header-actions">
        <Button
          label="Apply Rules"
          icon="pi pi-play"
          severity="secondary"
          size="small"
          :loading="isApplying"
          :disabled="isApplying || rules.length === 0"
          @click="handleApplyRules"
        />
        <Button
          label="Create Rule"
          icon="pi pi-plus"
          size="small"
          @click="handleCreate"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <i class="pi pi-spin pi-spinner loading-icon"></i>
      <p>Loading rules...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="rules.length === 0" class="empty-state">
      <i class="pi pi-list-check empty-icon"></i>
      <h4>No rules yet</h4>
      <p>Rules automatically tag transactions based on conditions you define.</p>
      <Button
        label="Create your first rule"
        icon="pi pi-plus"
        @click="handleCreate"
      />
    </div>

    <!-- Rules Table -->
    <div v-else class="rules-table-container">
      <table class="rules-table">
        <thead>
          <tr>
            <th class="col-name">Name</th>
            <th class="col-conditions">Conditions</th>
            <th class="col-tag">Tag</th>
            <th class="col-active">Active</th>
            <th class="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rule in rules" :key="rule.rule_id">
            <td class="col-name">{{ rule.name }}</td>
            <td class="col-conditions">
              <span class="conditions-summary">{{ formatConditions(rule) }}</span>
            </td>
            <td class="col-tag">
              <span
                v-if="getTagForRule(rule)"
                class="tag-chip"
                :style="{ backgroundColor: getTagForRule(rule)?.color || '#6B7280' }"
              >
                {{ getTagForRule(rule)?.label }}
              </span>
              <span v-else class="no-tag">No tag</span>
            </td>
            <td class="col-active">
              <InputSwitch
                :modelValue="rule.is_active"
                :disabled="togglingRules.has(rule.rule_id)"
                @update:modelValue="handleToggle(rule, $event)"
              />
            </td>
            <td class="col-actions">
              <Button
                icon="pi pi-pencil"
                severity="secondary"
                text
                rounded
                size="small"
                @click="handleEdit(rule)"
                aria-label="Edit rule"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                size="small"
                @click="handleDelete(rule)"
                aria-label="Delete rule"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Rule Form Modal -->
    <RuleFormModal
      :visible="showRuleModal"
      :rule="editingRule"
      @update:visible="handleModalClose"
      @saved="handleRuleSaved"
    />

    <!-- Delete Confirm Dialog -->
    <DeleteConfirmDialog
      :visible="showDeleteDialog"
      title="Delete Rule"
      :message="`Are you sure you want to delete the rule '${deletingRule?.name}'?`"
      :loading="isDeleting"
      @update:visible="handleDeleteCancel"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped>
.rules-tab {
  padding: 24px 0;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.tab-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6b7280;
}

.loading-icon {
  font-size: 32px;
  margin-bottom: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: #d1d5db;
  margin-bottom: 16px;
}

.empty-state h4 {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 8px 0;
}

.empty-state p {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 24px 0;
  max-width: 320px;
}

.rules-table-container {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.rules-table {
  width: 100%;
  border-collapse: collapse;
}

.rules-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.rules-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
  vertical-align: middle;
}

.rules-table tr:last-child td {
  border-bottom: none;
}

.rules-table tr:hover td {
  background: #f9fafb;
}

.col-name {
  width: 180px;
  font-weight: 500;
}

.col-conditions {
  width: auto;
}

.col-tag {
  width: 120px;
}

.col-active {
  width: 80px;
  text-align: center;
}

.col-actions {
  width: 100px;
  text-align: right;
}

.conditions-summary {
  font-size: 13px;
  color: #4b5563;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.tag-chip {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
}

.no-tag {
  font-size: 13px;
  color: #9ca3af;
  font-style: italic;
}
</style>
