<script setup lang="ts">
import { ref, computed } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useCreditCards, CardBrand, type CreditCard } from '@/composables/useCreditCards'

interface Props {
  visible: boolean
  existingCards: CreditCard[]
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'card-created', card: CreditCard): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { createCard } = useCreditCards()

// Form field state
const bank = ref<string>('')
const brand = ref<CardBrand | null>(null)
const last4 = ref<string>('')
const alias = ref<string>('')

// UX state
const formSubmitted = ref<boolean>(false)
const isSubmitting = ref<boolean>(false)
const serverError = ref<string | null>(null)

// Provider/brand dropdown options
const brandOptions = [
  { label: 'Visa', value: CardBrand.VISA },
  { label: 'Mastercard', value: CardBrand.MASTERCARD },
  { label: 'American Express', value: CardBrand.AMEX },
  { label: 'Discover', value: CardBrand.DISCOVER },
  { label: 'Other', value: CardBrand.OTHER },
]

/**
 * Normalize bank name for comparison (trim, collapse whitespace, lowercase)
 */
const normalizeBankName = (name: string): string => {
  return name.trim().replace(/\s+/g, ' ').toLowerCase()
}

/**
 * Check if a card with the same bank+brand+last4 already exists
 */
const duplicateCard = computed((): CreditCard | null => {
  if (!bank.value || !brand.value || !last4.value) {
    return null
  }

  const normalizedBank = normalizeBankName(bank.value)
  return (
    props.existingCards.find(
      (card) =>
        normalizeBankName(card.bank) === normalizedBank &&
        card.brand === brand.value &&
        card.last4 === last4.value
    ) || null
  )
})

/**
 * Computed validation errors (shows only after formSubmitted)
 */
const bankError = computed((): string | null => {
  if (!formSubmitted.value) return null
  if (!bank.value || bank.value.trim() === '') {
    return 'Bank name is required'
  }
  return null
})

const brandError = computed((): string | null => {
  if (!formSubmitted.value) return null
  if (!brand.value) {
    return 'Please select a provider'
  }
  return null
})

const last4Error = computed((): string | null => {
  if (!formSubmitted.value) return null
  if (!last4.value || last4.value.trim() === '') {
    return 'Last 4 digits are required'
  }
  if (!/^\d{4}$/.test(last4.value)) {
    return 'Must be exactly 4 digits'
  }
  return null
})

const duplicateError = computed((): string | null => {
  if (!formSubmitted.value) return null
  return duplicateCard.value ? 'A card with this bank, provider, and last 4 digits already exists' : null
})

/**
 * Overall form validity (blocks submission)
 */
const isFormValid = computed((): boolean => {
  return (
    !bankError.value &&
    !brandError.value &&
    !last4Error.value &&
    !duplicateError.value
  )
})

/**
 * Update modal visibility, ensuring all close paths go through one function.
 * Resets form state before emitting visibility change.
 */
function setVisible(value: boolean): void {
  if (!value) {
    // Reset form state when closing
    bank.value = ''
    brand.value = null
    last4.value = ''
    alias.value = ''
    formSubmitted.value = false
    serverError.value = null
    isSubmitting.value = false
  }
  emit('update:visible', value)
}

// Internal visible state that syncs with prop
const internalVisible = computed({
  get: () => props.visible,
  set: setVisible
})

/**
 * Handle save button click - validates and submits form
 */
async function handleSave(): Promise<void> {
  formSubmitted.value = true
  serverError.value = null

  // Don't call API if validation fails
  if (!isFormValid.value) {
    return
  }

  if (!brand.value) {
    return // Should never happen due to validation
  }

  isSubmitting.value = true

  try {
    const createdCard = await createCard({
      bank: bank.value.trim(),
      brand: brand.value,
      last4: last4.value,
      alias: alias.value.trim() || undefined,
    })

    // Emit success and close modal (reset happens in setVisible)
    emit('card-created', createdCard)
    setVisible(false)
  } catch (e) {
    // Keep modal open, show server error
    serverError.value = e instanceof Error ? e.message : 'Failed to create card'
  } finally {
    isSubmitting.value = false
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
    header="Add Card"
    :style="{ width: '500px' }"
    :breakpoints="{ '640px': '90vw' }"
    :closable="!isSubmitting"
    :dismissableMask="!isSubmitting"
    :draggable="false"
  >
    <div class="add-card-form">
      <!-- Server Error Message -->
      <Message v-if="serverError" severity="error" :closable="false" class="server-error">
        {{ serverError }}
      </Message>

      <!-- Bank Name Field -->
      <div class="form-field">
        <label for="bank-input" class="field-label">Bank Name</label>
        <InputText
          id="bank-input"
          v-model="bank"
          :disabled="isSubmitting"
          :class="{ 'p-invalid': !!bankError }"
          placeholder="e.g., Chase, Wells Fargo"
          class="w-full"
        />
        <small v-if="bankError" class="p-error">{{ bankError }}</small>
      </div>

      <!-- Provider/Brand Field -->
      <div class="form-field">
        <label for="brand-select" class="field-label">Provider</label>
        <Dropdown
          id="brand-select"
          v-model="brand"
          :options="brandOptions"
          option-label="label"
          option-value="value"
          placeholder="Select a provider"
          :disabled="isSubmitting"
          :class="{ 'p-invalid': !!brandError }"
          class="w-full"
        />
        <small v-if="brandError" class="p-error">{{ brandError }}</small>
      </div>

      <!-- Last 4 Digits Field -->
      <div class="form-field">
        <label for="last4-input" class="field-label">Last 4 Digits</label>
        <InputText
          id="last4-input"
          v-model="last4"
          maxlength="4"
          inputmode="numeric"
          placeholder="1234"
          :disabled="isSubmitting"
          :class="{ 'p-invalid': !!last4Error }"
          class="w-full"
        />
        <small v-if="last4Error" class="p-error">{{ last4Error }}</small>
      </div>

      <!-- Alias Field (Optional) -->
      <div class="form-field">
        <label for="alias-input" class="field-label">Alias (Optional)</label>
        <InputText
          id="alias-input"
          v-model="alias"
          :disabled="isSubmitting"
          placeholder="e.g., Personal Chase Card"
          class="w-full"
        />
        <small class="field-hint">A friendly name for this card</small>
      </div>

      <!-- Duplicate Error Message -->
      <Message v-if="duplicateError" severity="warn" :closable="false" class="duplicate-warning">
        {{ duplicateError }}
      </Message>
    </div>

    <template #footer>
      <div class="modal-footer">
        <Button
          label="Cancel"
          severity="secondary"
          outlined
          :disabled="isSubmitting"
          @click="handleCancel"
        />
        <Button
          label="Save"
          icon="pi pi-check"
          :loading="isSubmitting"
          :disabled="isSubmitting"
          @click="handleSave"
        />
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
.add-card-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.server-error {
  margin-bottom: 0;
}

.duplicate-warning {
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

.field-hint {
  font-size: 0.75rem;
  color: var(--text-color-secondary);
  margin-top: -0.25rem;
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
