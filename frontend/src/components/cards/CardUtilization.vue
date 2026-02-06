<script setup lang="ts">
/**
 * CardUtilization Component
 *
 * Displays credit limit, outstanding balance, and utilization percentage for a credit card.
 * Shows a progress bar visualization and a "Set Limit" button when no limit is set.
 */

import { computed } from 'vue'
import type { CreditCard } from '@/composables/useCreditCards'
import ProgressBar from 'primevue/progressbar'
import Button from 'primevue/button'

// Props
interface Props {
  card: CreditCard
  formatCurrency?: (amount: number | string | null | undefined) => string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'set-limit': [card: CreditCard]
}>()

// Computed values
const hasLimit = computed(() => {
  return props.card.credit_limit !== null && props.card.credit_limit > 0
})

const utilizationRaw = computed(() => {
  if (!hasLimit.value) return null
  // We know credit_limit is not null here because hasLimit.value is true
  const limit = props.card.credit_limit!
  return (props.card.outstanding_balance / limit) * 100
})

const utilizationDisplay = computed(() => {
  if (utilizationRaw.value === null) return 'N/A'
  return `${utilizationRaw.value.toFixed(1)}%`
})

const progressValue = computed(() => {
  if (utilizationRaw.value === null) return 0
  // Clamp between 0 and 100 for display (handles over-limit and negative balances)
  return Math.max(0, Math.min(100, utilizationRaw.value))
})

const limitDisplay = computed(() => {
  if (!hasLimit.value) return 'Not set'
  return props.formatCurrency ? props.formatCurrency(props.card.credit_limit!) : `$${props.card.credit_limit!.toFixed(2)}`
})

const balanceDisplay = computed(() => {
  return props.formatCurrency ? props.formatCurrency(props.card.outstanding_balance) : `$${props.card.outstanding_balance.toFixed(2)}`
})

// Handlers
const handleSetLimit = () => {
  emit('set-limit', props.card)
}
</script>

<template>
  <div class="card-utilization">
    <div class="utilization-info">
      <div class="info-row">
        <span class="info-label">Credit Limit</span>
        <span class="info-value" data-testid="credit-limit">{{ limitDisplay }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Outstanding Balance</span>
        <span class="info-value" data-testid="outstanding-balance">{{ balanceDisplay }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Utilization</span>
        <span class="info-value" data-testid="utilization">{{ utilizationDisplay }}</span>
      </div>
    </div>

    <ProgressBar
      :value="progressValue"
      :showValue="false"
      class="utilization-progress"
      data-testid="progress-bar"
    />

    <Button
      v-if="!hasLimit"
      label="Set Limit"
      outlined
      size="small"
      class="set-limit-button"
      @click="handleSetLimit"
      data-testid="set-limit-button"
    />
  </div>
</template>

<style scoped>
.card-utilization {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.utilization-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.8;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  font-weight: 600;
}

.utilization-progress {
  margin-top: 8px;
}

.set-limit-button {
  width: 100%;
  font-size: 13px;
  padding: 8px 16px;
}
</style>
