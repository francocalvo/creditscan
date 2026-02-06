<script setup lang="ts">
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Calendar from 'primevue/calendar'
import Button from 'primevue/button'
import {
  type RuleConditionCreate,
  type ConditionField,
  type ConditionOperator,
} from '@/api/types.gen'

interface Props {
  conditions: RuleConditionCreate[]
}

interface Emits {
  (e: 'update:conditions', value: RuleConditionCreate[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

/**
 * Available fields for conditions
 */
const fieldOptions = [
  { label: 'Payee', value: 'payee' },
  { label: 'Description', value: 'description' },
  { label: 'Amount', value: 'amount' },
  { label: 'Date', value: 'date' },
]

/**
 * Operator options by field type
 */
const textOperators = [
  { label: 'Contains', value: 'contains' },
  { label: 'Equals', value: 'equals' },
]

const amountOperators = [
  { label: 'Equals', value: 'equals' },
  { label: 'Greater than (>)', value: 'gt' },
  { label: 'Greater or equal (>=)', value: 'gte' },
  { label: 'Less than (<)', value: 'lt' },
  { label: 'Less or equal (<=)', value: 'lte' },
  { label: 'Between', value: 'between' },
]

const dateOperators = [
  { label: 'Before', value: 'before' },
  { label: 'After', value: 'after' },
  { label: 'Between', value: 'between' },
]

/**
 * Get the field type (text, number, date) for a field
 */
function getFieldType(field: ConditionField): 'text' | 'number' | 'date' {
  if (field === 'amount') return 'number'
  if (field === 'date') return 'date'
  return 'text'
}

/**
 * Get available operators for a specific field
 */
function getOperatorsForField(field: ConditionField) {
  const fieldType = getFieldType(field)
  if (fieldType === 'text') return textOperators
  if (fieldType === 'number') return amountOperators
  return dateOperators
}

/**
 * Get the default operator for a field
 */
function getDefaultOperator(field: ConditionField): ConditionOperator {
  const fieldType = getFieldType(field)
  if (fieldType === 'text') return 'contains'
  if (fieldType === 'number') return 'equals'
  return 'after'
}

/**
 * Add a new condition to the list
 */
function addCondition(): void {
  const newCondition: RuleConditionCreate = {
    field: 'payee',
    operator: 'contains',
    value: '',
    logical_operator: 'AND',
  }
  emit('update:conditions', [...props.conditions, newCondition])
}

/**
 * Remove a condition at the specified index
 */
function removeCondition(index: number): void {
  const updated = props.conditions.filter((_, i) => i !== index)
  emit('update:conditions', updated)
}

/**
 * Update a specific condition
 */
function updateCondition(index: number, updates: Partial<RuleConditionCreate>): void {
  const updated = props.conditions.map((condition, i) =>
    i === index ? { ...condition, ...updates } : condition
  )
  emit('update:conditions', updated)
}

/**
 * Handle field change - reset operator and values if needed
 */
function handleFieldChange(index: number, newField: ConditionField): void {
  const currentCondition = props.conditions[index]
  if (!currentCondition) return

  // Check if current operator is compatible with new field
  const compatibleOperators = getOperatorsForField(newField)
  const currentOperator = compatibleOperators.find((op) => op.value === currentCondition.operator)

  if (!currentOperator) {
    // Reset to default operator if incompatible
    const defaultOp = getDefaultOperator(newField)
    updateCondition(index, {
      field: newField,
      operator: defaultOp,
      value: '',
      value_secondary: null,
    })
  } else {
    // Just update the field
    updateCondition(index, { field: newField })
  }
}

/**
 * Parse date string to Date object
 */
function parseDate(dateString: string): Date | null {
  if (!dateString) return null
  return new Date(dateString)
}

/**
 * Get display value for a condition's value (for number field)
 */
function getNumberValue(condition: RuleConditionCreate): number | null {
  if (condition.value === null || condition.value === undefined || condition.value === '') {
    return null
  }
  const parsed = parseFloat(condition.value)
  return isNaN(parsed) ? null : parsed
}

/**
 * Get display value for a condition's value (for date field)
 */
function getDateValue(condition: RuleConditionCreate): Date | null {
  if (!condition.value) return null
  return parseDate(condition.value)
}

/**
 * Get display value for a condition's value (for text field)
 */
function getTextValue(condition: RuleConditionCreate): string {
  return condition.value ?? ''
}

/**
 * Get display value for a condition's secondary value (for number field)
 */
function getSecondaryNumberValue(condition: RuleConditionCreate): number | null {
  if (!condition.value_secondary || condition.value_secondary === '') {
    return null
  }
  const parsed = parseFloat(condition.value_secondary)
  return isNaN(parsed) ? null : parsed
}

/**
 * Get display value for a condition's secondary value (for date field)
 */
function getSecondaryDateValue(condition: RuleConditionCreate): Date | null {
  if (!condition.value_secondary) return null
  return parseDate(condition.value_secondary)
}

/**
 * Get display value for a condition's secondary value (for text field)
 */
function getSecondaryTextValue(condition: RuleConditionCreate): string {
  return condition.value_secondary ?? ''
}

/**
 * Emit value update
 */
function updateValue(index: number, value: string | number | Date | null): void {
  const condition = props.conditions[index]
  if (!condition) return

  let formattedValue: string
  if (condition.field === 'amount') {
    formattedValue = value !== null && value !== '' ? String(value) : ''
  } else if (condition.field === 'date' && value instanceof Date) {
    const isoString = value.toISOString().split('T')[0]
    formattedValue = isoString ?? ''
  } else if (value === null) {
    formattedValue = ''
  } else {
    formattedValue = String(value)
  }

  updateCondition(index, { value: formattedValue })
}

/**
 * Wrapper for InputText update event (handles undefined)
 */
function handleTextUpdate(index: number, value: string | undefined): void {
  updateValue(index, value ?? '')
}

/**
 * Wrapper for InputNumber update event
 */
function handleNumberUpdate(index: number, value: number | null): void {
  updateValue(index, value)
}

/**
 * Wrapper for Calendar update event (handles arrays)
 */
function handleDateUpdate(index: number, value: Date | Date[] | (Date | null)[] | null | undefined): void {
  // If value is an array, take the first date
  const date = Array.isArray(value) ? value[0] : value
  updateValue(index, date ?? null)
}

/**
 * Wrapper for secondary value InputText update event
 */
function handleSecondaryTextUpdate(index: number, value: string | undefined): void {
  updateSecondaryValue(index, value ?? '')
}

/**
 * Wrapper for secondary value InputNumber update event
 */
function handleSecondaryNumberUpdate(index: number, value: number | null): void {
  updateSecondaryValue(index, value)
}

/**
 * Wrapper for secondary value Calendar update event
 */
function handleSecondaryDateUpdate(index: number, value: Date | Date[] | (Date | null)[] | null | undefined): void {
  // If value is an array, take the first date
  const date = Array.isArray(value) ? value[0] : value
  updateSecondaryValue(index, date ?? null)
}

/**
 * Emit secondary value update
 */
function updateSecondaryValue(index: number, value: string | number | Date | null): void {
  const condition = props.conditions[index]
  if (!condition) return

  let formattedValue: string | null = null
  if (value !== null && value !== '') {
    if (condition.field === 'amount') {
      formattedValue = String(value)
    } else if (condition.field === 'date' && value instanceof Date) {
      const isoString = value.toISOString().split('T')[0]
      formattedValue = isoString ?? null
    } else {
      formattedValue = String(value)
    }
  }

  updateCondition(index, { value_secondary: formattedValue })
}
</script>

<template>
  <div class="condition-builder">
    <div v-for="(condition, index) in conditions" :key="index" class="condition-row">
      <!-- Logical operator toggle shown before all but first condition -->
      <button
        v-if="index > 0"
        type="button"
        class="logical-operator-toggle"
        @click="updateCondition(index, { logical_operator: condition.logical_operator === 'OR' ? 'AND' : 'OR' })"
      >
        {{ condition.logical_operator || 'AND' }}
      </button>

      <!-- Field dropdown -->
      <Dropdown
        :modelValue="condition.field"
        :options="fieldOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Select field"
        :disabled="conditions.length === 0"
        @update:modelValue="handleFieldChange(index, $event)"
      />

      <!-- Operator dropdown -->
      <Dropdown
        :modelValue="condition.operator"
        :options="getOperatorsForField(condition.field)"
        optionLabel="label"
        optionValue="value"
        placeholder="Select operator"
        :disabled="conditions.length === 0"
        @update:modelValue="updateCondition(index, { operator: $event })"
      />

      <!-- Value input (type varies by field) -->
      <template v-if="getFieldType(condition.field) === 'text'">
        <InputText
          :modelValue="getTextValue(condition)"
          placeholder="Value"
          class="value-input"
          @update:modelValue="handleTextUpdate(index, $event)"
        />
      </template>

      <template v-else-if="getFieldType(condition.field) === 'number'">
        <InputNumber
          :modelValue="getNumberValue(condition)"
          placeholder="Amount"
          mode="currency"
          currency="USD"
          class="value-input"
          @update:modelValue="handleNumberUpdate(index, $event)"
        />
      </template>

      <template v-else-if="getFieldType(condition.field) === 'date'">
        <Calendar
          :modelValue="getDateValue(condition)"
          dateFormat="yy-mm-dd"
          placeholder="Select date"
          showIcon
          class="value-input"
          @update:modelValue="handleDateUpdate(index, $event)"
        />
      </template>

      <!-- Secondary value for 'between' operator -->
      <template v-if="condition.operator === 'between'">
        <span class="between-separator">and</span>

        <template v-if="getFieldType(condition.field) === 'text'">
          <InputText
            :modelValue="getSecondaryTextValue(condition)"
            placeholder="Value"
            class="value-input value-input--secondary"
            @update:modelValue="handleSecondaryTextUpdate(index, $event)"
          />
        </template>

        <template v-else-if="getFieldType(condition.field) === 'number'">
          <InputNumber
            :modelValue="getSecondaryNumberValue(condition)"
            placeholder="Amount"
            mode="currency"
            currency="USD"
            class="value-input value-input--secondary"
            @update:modelValue="handleSecondaryNumberUpdate(index, $event)"
          />
        </template>

        <template v-else-if="getFieldType(condition.field) === 'date'">
          <Calendar
            :modelValue="getSecondaryDateValue(condition)"
            dateFormat="yy-mm-dd"
            placeholder="Select date"
            showIcon
            class="value-input value-input--secondary"
            @update:modelValue="handleSecondaryDateUpdate(index, $event)"
          />
        </template>
      </template>

      <!-- Remove button -->
      <Button
        icon="pi pi-trash"
        severity="danger"
        text
        rounded
        size="small"
        :disabled="conditions.length === 1"
        aria-label="Remove condition"
        @click="removeCondition(index)"
      />
    </div>

    <!-- Add condition button -->
    <Button
      label="Add Condition"
      icon="pi pi-plus"
      severity="secondary"
      outlined
      size="small"
      @click="addCondition"
    />
  </div>
</template>

<style scoped>
.condition-builder {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.condition-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.logical-operator-toggle {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary-color);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: var(--surface-ground);
  border: 1px solid var(--surface-border);
  border-radius: 4px;
  padding: 2px 8px;
  cursor: pointer;
  transition: background-color 0.15s ease;
  min-width: 40px;
  text-align: center;
}

.logical-operator-toggle:hover {
  background: var(--surface-hover);
}

.value-input {
  flex: 1;
  min-width: 160px;
}

.value-input--secondary {
  min-width: 140px;
}

.between-separator {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

/* PrimeVue overrides for smaller dropdowns in this component */
.condition-row :deep(.p-dropdown) {
  min-width: 140px;
}
</style>
