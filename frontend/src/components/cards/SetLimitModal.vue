<script setup lang="ts">
/**
 * SetLimitModal Component
 *
 * Modal dialog for setting or updating a credit card's credit limit.
 * Pre-fills with existing limit, validates input, and saves via parent callback.
 */

import { ref, watch, computed } from 'vue'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import Message from 'primevue/message'
import type { CreditCard } from '@/composables/useCreditCards'

interface Props {
  card: CreditCard | null
  modelValue: boolean
  onSave: (cardId: string, creditLimit: number) => Promise<void>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()

// Local state
const creditLimit = ref<number | null>(null)
const isLoading = ref(false)
const validationError = ref<string | null>(null)
const apiError = ref<string | null>(null)

// Pre-fill when modal opens with a card
watch(
  () => ({ card: props.card, visible: props.modelValue }),
  ({ card, visible }) => {
    if (visible && card) {
      // Pre-fill with existing limit if available and valid (> 0)
      creditLimit.value = card.credit_limit && card.credit_limit > 0 ? card.credit_limit : null
    } else if (!visible) {
      // Clear state when modal closes
      creditLimit.value = null
      validationError.value = null
      apiError.value = null
    }
  },
  { immediate: true, deep: true },
)

// Clear errors when input changes
watch(creditLimit, () => {
  validationError.value = null
  apiError.value = null
})

// Validate input
const isValid = computed(() => {
  return (
    props.card !== null &&
    creditLimit.value !== null &&
    creditLimit.value > 0 &&
    Number.isFinite(creditLimit.value)
  )
})

// Handle save
const handleSave = async () => {
  if (!props.card || creditLimit.value === null) return

  // Validate input
  if (creditLimit.value <= 0) {
    validationError.value = 'Credit limit must be greater than 0'
    return
  }

  if (!Number.isFinite(creditLimit.value)) {
    validationError.value = 'Please enter a valid number'
    return
  }

  isLoading.value = true
  apiError.value = null
  validationError.value = null

  try {
    await props.onSave(props.card.id, creditLimit.value)
    // Success: emit saved and close modal
    emit('saved')
    emit('update:modelValue', false)
  } catch (error) {
    // Error: display API error
    apiError.value = error instanceof Error ? error.message : 'Failed to save credit limit'
  } finally {
    isLoading.value = false
  }
}

// Handle cancel/close
const handleClose = () => {
  if (isLoading.value) return
  emit('update:modelValue', false)
}
</script>

<template>
  <Dialog
    :visible="modelValue"
    modal
    header="Set Credit Limit"
    :style="{ width: '450px' }"
    :closable="!isLoading"
    @update:visible="handleClose"
  >
    <div v-if="card" class="modal-content">
      <!-- Card identity -->
      <div class="card-identity">
        <div class="card-info">
          <span class="card-bank">{{ card.bank }}</span>
          <span class="card-last4">••{{ card.last4 }}</span>
        </div>
      </div>

      <!-- Error messages -->
      <Message
        v-if="validationError"
        severity="error"
        :closable="false"
        class="error-message"
      >
        {{ validationError }}
      </Message>
      <Message
        v-if="apiError"
        severity="error"
        :closable="false"
        class="error-message"
      >
        {{ apiError }}
      </Message>

      <!-- Form -->
      <div class="form-group">
        <label for="credit-limit" class="form-label">Credit Limit</label>
        <InputNumber
          id="credit-limit"
          v-model="creditLimit"
          mode="currency"
          currency="USD"
          :min="0.01"
          :min-fraction-digits="2"
          :max-fraction-digits="2"
          :disabled="isLoading"
          placeholder="Enter credit limit"
          class="input-field"
          data-testid="credit-limit-input"
        />
        <small class="form-hint">
          Enter the credit limit for this card. Must be greater than 0.
        </small>
      </div>

      <!-- Buttons -->
      <div class="button-group">
        <Button
          label="Cancel"
          outlined
          :disabled="isLoading"
          @click="handleClose"
          class="cancel-button"
          data-testid="cancel-button"
        />
        <Button
          label="Save"
          :loading="isLoading"
          :disabled="!isValid"
          @click="handleSave"
          class="save-button"
          data-testid="save-button"
        />
      </div>
    </div>
  </Dialog>
</template>

<style scoped>
.modal-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-identity {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 8px;
}

.card-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-heading);
}

.card-bank {
  font-weight: 600;
}

.card-last4 {
  color: var(--text-muted);
}

.error-message {
  margin: 8px 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-body);
}

.input-field {
  width: 100%;
}

.form-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.button-group {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.cancel-button {
  min-width: 100px;
}

.save-button {
  min-width: 100px;
}
</style>
