<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useRules, type RulePublic } from '@/composables/useRules'
import { useTags, type Tag } from '@/composables/useTags'
import { type RuleConditionCreate } from '@/api/types.gen'
import ConditionBuilder from './ConditionBuilder.vue'

interface Props {
  visible: boolean
  rule: RulePublic | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'saved'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { createRule, updateRule } = useRules()
const { tags } = useTags()

// Form state
const name = ref('')
const conditions = ref<RuleConditionCreate[]>([])
const tagId = ref('')

// UX state
const formSubmitted = ref(false)
const isSaving = ref(false)
const serverError = ref<string | null>(null)

/**
 * Whether modal is in edit mode (rule prop is provided)
 */
const isEditMode = computed(() => props.rule !== null)

/**
 * Dialog header text
 */
const dialogHeader = computed(() => (isEditMode.value ? 'Edit Rule' : 'Create Rule'))

/**
 * Save button label
 */
const saveButtonLabel = computed(() => (isEditMode.value ? 'Save' : 'Create'))

/**
 * Name validation error
 */
const nameError = computed((): string | null => {
  if (!formSubmitted.value) return null
  const trimmed = name.value.trim()
  if (!trimmed) {
    return 'Name is required'
  }
  if (trimmed.length > 100) {
    return 'Name must be 100 characters or less'
  }
  return null
})

/**
 * Conditions validation error
 */
const conditionsError = computed((): string | null => {
  if (!formSubmitted.value) return null
  if (conditions.value.length === 0) {
    return 'At least one condition is required'
  }
  // Check if all conditions have required fields filled
  for (const condition of conditions.value) {
    if (!condition.value || condition.value.trim() === '') {
      return 'All conditions must have a value'
    }
    if (condition.operator === 'between' && (!condition.value_secondary || condition.value_secondary.trim() === '')) {
      return 'Between operator requires both values'
    }
  }
  return null
})

/**
 * Tag validation error
 */
const tagError = computed((): string | null => {
  if (!formSubmitted.value) return null
  if (!tagId.value) {
    return 'Tag is required'
  }
  return null
})

/**
 * Form validity
 */
const isFormValid = computed(() => !nameError.value && !conditionsError.value && !tagError.value)

/**
 * Get selected tag object for display
 */
function getSelectedTag(): Tag | undefined {
  return tags.value.find((tag) => tag.tag_id === tagId.value)
}

/**
 * Reset form to initial state
 */
function resetForm(): void {
  name.value = ''
  conditions.value = []
  tagId.value = ''
  formSubmitted.value = false
  serverError.value = null
  isSaving.value = false
}

/**
 * Populate form with rule data for editing
 */
function populateForm(rule: RulePublic): void {
  name.value = rule.name

  // Map RuleConditionPublic to RuleConditionCreate format
  const sortedConditions = [...rule.conditions].sort((a, b) => a.position - b.position)
  conditions.value = sortedConditions.map((c) => ({
    field: c.field,
    operator: c.operator,
    value: c.value,
    value_secondary: c.value_secondary,
    logical_operator: c.logical_operator,
  }))

  // Get tag from first action
  const firstAction = rule.actions[0]
  tagId.value = firstAction?.tag_id || ''
}

/**
 * Watch for visibility changes to reset/populate form
 */
watch(
  () => props.visible,
  (newVisible) => {
    if (newVisible) {
      resetForm()
      if (props.rule) {
        populateForm(props.rule)
      } else {
        // Initialize with one default condition for create mode
        conditions.value = [
          {
            field: 'payee',
            operator: 'contains',
            value: '',
            logical_operator: 'AND',
          },
        ]
      }
    }
  }
)

/**
 * Update modal visibility
 */
function setVisible(value: boolean): void {
  emit('update:visible', value)
}

// Internal visible state that syncs with prop
const internalVisible = computed({
  get: () => props.visible,
  set: setVisible,
})

/**
 * Handle save button click
 */
async function handleSave(): Promise<void> {
  formSubmitted.value = true
  serverError.value = null

  if (!isFormValid.value) {
    return
  }

  isSaving.value = true

  try {
    // Build condition array with proper logical operators
    const conditionsWithLogicalOperator = conditions.value.map((c, index) => ({
      ...c,
      logical_operator: index === 0 ? 'AND' : (c.logical_operator || 'AND'),
    }))

    const payload = {
      name: name.value.trim(),
      is_active: true,
      conditions: conditionsWithLogicalOperator,
      actions: [
        {
          action_type: 'add_tag' as const,
          tag_id: tagId.value,
        },
      ],
    }

    if (isEditMode.value && props.rule) {
      await updateRule(props.rule.rule_id, payload)
    } else {
      await createRule(payload)
    }

    emit('saved')
    setVisible(false)
  } catch (e) {
    serverError.value = e instanceof Error ? e.message : 'Failed to save rule'
  } finally {
    isSaving.value = false
  }
}

/**
 * Handle cancel button click
 */
function handleCancel(): void {
  setVisible(false)
}
</script>

<template>
  <Dialog
    v-model:visible="internalVisible"
    modal
    :header="dialogHeader"
    :style="{ width: '600px' }"
    :breakpoints="{ '640px': '90vw' }"
    :closable="!isSaving"
    :dismissableMask="!isSaving"
    :draggable="false"
  >
    <div class="rule-form">
      <!-- Server Error Message -->
      <Message v-if="serverError" severity="error" :closable="false" class="server-error">
        {{ serverError }}
      </Message>

      <!-- Name field -->
      <div class="form-field">
        <label for="rule-name-input" class="field-label">Name</label>
        <InputText
          id="rule-name-input"
          v-model="name"
          :disabled="isSaving"
          :class="{ 'p-invalid': !!nameError }"
          placeholder="e.g., Supermarket Purchases"
          class="w-full"
          maxlength="100"
        />
        <small v-if="nameError" class="p-error">{{ nameError }}</small>
      </div>

      <!-- Conditions section -->
      <div class="form-field">
        <label class="field-label">Conditions</label>
        <ConditionBuilder v-model:conditions="conditions" />
        <small v-if="conditionsError" class="p-error">{{ conditionsError }}</small>
      </div>

      <!-- Tag selection -->
      <div class="form-field">
        <label for="rule-tag-select" class="field-label">Apply Tag</label>
        <Dropdown
          id="rule-tag-select"
          v-model="tagId"
          :options="tags"
          optionLabel="label"
          optionValue="tag_id"
          placeholder="Select a tag"
          :disabled="isSaving"
          :class="{ 'p-invalid': !!tagError }"
          class="w-full"
        >
          <template #option="{ option }">
            <div class="tag-option">
              <span class="tag-dot" :style="{ backgroundColor: option.color || '#6B7280' }"></span>
              {{ option.label }}
            </div>
          </template>
          <template #value="{ value }">
            <div v-if="value" class="tag-option">
              <span class="tag-dot" :style="{ backgroundColor: getSelectedTag()?.color || '#6B7280' }"></span>
              {{ getSelectedTag()?.label }}
            </div>
            <span v-else>Select a tag</span>
          </template>
        </Dropdown>
        <small v-if="tagError" class="p-error">{{ tagError }}</small>
      </div>
    </div>

    <template #footer>
      <div class="modal-footer">
        <Button
          label="Cancel"
          severity="secondary"
          outlined
          :disabled="isSaving"
          @click="handleCancel"
        />
        <Button
          :label="saveButtonLabel"
          icon="pi pi-check"
          :loading="isSaving"
          :disabled="isSaving"
          @click="handleSave"
        />
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
.rule-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.server-error {
  margin-bottom: 0;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-color);
}

.tag-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tag-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.w-full {
  width: 100%;
}
</style>
