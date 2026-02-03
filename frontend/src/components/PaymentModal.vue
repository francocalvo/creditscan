<script setup lang="ts">
import { ref, computed, watch, withDefaults } from 'vue'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Calendar from 'primevue/calendar'
import Message from 'primevue/message'

interface Props {
  visible: boolean
  statementId: string
  currentBalance: number | null
  statementCard?: string
  isSubmitting?: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'submit', paymentData: PaymentData): void
  (e: 'edit-statement'): void
}

interface PaymentData {
  statement_id: string
  amount: number
  payment_date: string
  currency: string
}

const props = withDefaults(defineProps<Props>(), {
  isSubmitting: false
})
const emit = defineEmits<Emits>()

const payInFull = ref(false)
const paymentAmount = ref<number | null>(null)
const paymentDate = ref<Date>(new Date())
const currency = ref('USD')
const error = ref<string | null>(null)

// Internal visible state that syncs with prop
const internalVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => {
    emit('update:visible', value)
  }
})

// Watch for pay in full toggle
watch(payInFull, (newValue) => {
  if (newValue && props.currentBalance !== null && typeof props.currentBalance === 'number') {
    paymentAmount.value = props.currentBalance
  } else if (!newValue) {
    paymentAmount.value = null
  }
})

// Watch for modal visibility reset
watch(() => props.visible, (newValue) => {
  if (newValue) {
    // Reset form when modal opens
    payInFull.value = false
    paymentAmount.value = null
    paymentDate.value = new Date()
    currency.value = 'USD'
    error.value = null
  }
})

const isFormValid = computed(() => {
  return paymentAmount.value !== null && 
         paymentAmount.value > 0 && 
         paymentDate.value !== null
})

const handleSubmit = () => {
  error.value = null

  if (!isFormValid.value) {
    error.value = 'Please fill in all required fields'
    return
  }

  if (paymentAmount.value === null) {
    error.value = 'Payment amount is required'
    return
  }

  if (props.currentBalance !== null && typeof props.currentBalance === 'number' && paymentAmount.value > props.currentBalance) {
    error.value = 'Payment amount cannot exceed the statement balance'
    return
  }

  const paymentData: PaymentData = {
    statement_id: props.statementId,
    amount: paymentAmount.value,
    payment_date: paymentDate.value.toISOString().split('T')[0],
    currency: currency.value
  }

  emit('submit', paymentData)
}

const handleEditStatement = () => {
  emit('edit-statement')
  internalVisible.value = false
}

const formatCurrency = (amount: number | null): string => {
  if (amount === null) return '$0.00'
  return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
</script>

<template>
  <Dialog
    v-model:visible="internalVisible"
    modal
    header="Make a Payment"
    :style="{ width: '500px' }"
    :closable="true"
    :draggable="false"
  >
    <div class="payment-modal-content">
      <div v-if="statementCard" class="statement-info">
        <p class="info-label">Statement:</p>
        <p class="info-value">{{ statementCard }}</p>
      </div>

      <div class="balance-info">
        <p class="info-label">Current Balance:</p>
        <p class="info-value balance-amount">{{ formatCurrency(currentBalance) }}</p>
      </div>

      <div class="form-field">
        <div class="checkbox-wrapper">
          <Checkbox
            v-model="payInFull"
            inputId="payInFull"
            :binary="true"
          />
          <label for="payInFull" class="checkbox-label">Pay in full</label>
        </div>
      </div>

      <div class="form-field">
        <label for="paymentAmount" class="field-label">
          Payment Amount <span class="required">*</span>
        </label>
        <InputNumber
          id="paymentAmount"
          v-model="paymentAmount"
          :disabled="payInFull"
          :min="0.01"
          :max="typeof props.currentBalance === 'number' ? props.currentBalance : undefined"
          mode="decimal"
          :minFractionDigits="2"
          :maxFractionDigits="2"
          currency="USD"
          prefix="$"
          class="w-full"
          :class="{ 'p-invalid': error && paymentAmount === null }"
          placeholder="0.00"
        />
        <small v-if="error && paymentAmount === null" class="error-text">
          {{ error }}
        </small>
      </div>

      <div class="form-field">
        <label for="paymentDate" class="field-label">
          Payment Date <span class="required">*</span>
        </label>
        <Calendar
          id="paymentDate"
          v-model="paymentDate"
          dateFormat="yy-mm-dd"
          :showIcon="true"
          class="w-full"
        />
      </div>

      <div class="form-field">
        <label for="currency" class="field-label">Currency</label>
        <select
          id="currency"
          v-model="currency"
          class="currency-select"
        >
          <option value="USD">USD</option>
          <option value="ARS">ARS</option>
        </select>
      </div>

      <Message v-if="error" severity="error" class="error-message">
        {{ error }}
      </Message>

      <div class="button-group">
        <Button
          label="Edit Statement"
          icon="pi pi-pencil"
          @click="handleEditStatement"
          :disabled="props.isSubmitting"
          severity="secondary"
          outlined
        />
        <Button
          label="Cancel"
          icon="pi pi-times"
          @click="internalVisible = false"
          :disabled="props.isSubmitting"
          severity="secondary"
          outlined
        />
        <Button
          label="Submit Payment"
          icon="pi pi-check"
          @click="handleSubmit"
          :loading="props.isSubmitting"
          :disabled="!isFormValid || props.isSubmitting"
        />
      </div>
    </div>
  </Dialog>
</template>

<style scoped>
.payment-modal-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 0.5rem 0;
}

.statement-info,
.balance-info {
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 8px;
  border: 1px solid var(--surface-border);
}

.info-label {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
  margin: 0 0 0.25rem 0;
  font-weight: 500;
}

.info-value {
  font-size: 1rem;
  color: var(--text-color);
  margin: 0;
  font-weight: 600;
}

.balance-amount {
  font-size: 1.5rem;
  color: var(--primary-color);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.checkbox-label {
  font-size: 0.938rem;
  color: var(--text-color);
  cursor: pointer;
  font-weight: 500;
}

.field-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.25rem;
}

.required {
  color: var(--red-500);
}

.error-text {
  color: var(--red-500);
  font-size: 0.875rem;
}

.currency-select {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  font-size: 0.938rem;
  background: var(--surface-card);
  color: var(--text-color);
  outline: none;
}

.currency-select:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px var(--primary-color-alpha-20);
}

.error-message {
  margin-top: 0.5rem;
}

.button-group {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.w-full {
  width: 100%;
}
</style>
