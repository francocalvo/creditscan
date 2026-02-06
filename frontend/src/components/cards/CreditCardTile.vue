<script setup lang="ts">
import { computed } from 'vue'
import type { CreditCard } from '@/composables/useCreditCards'
import { getCardBackgroundColor } from '@/utils/cardColors'

interface Props {
  card: CreditCard
  currentBalance?: number | string | null
  formatCurrency?: (amount: number | string | null | undefined) => string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'set-limit': [card: CreditCard]
}>()

const toFiniteNumber = (value: unknown, fallback = 0): number => {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : fallback
  }

  if (typeof value === 'string') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : fallback
  }

  return fallback
}

const formatAmount = (amount: number): string => {
  if (props.formatCurrency) {
    return props.formatCurrency(amount)
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

const hasLimit = computed(() => {
  return (
    typeof props.card.credit_limit === 'number' &&
    Number.isFinite(props.card.credit_limit) &&
    props.card.credit_limit > 0
  )
})

const currentBalanceValue = computed(() => toFiniteNumber(props.currentBalance, 0))

const outstandingBalanceValue = computed(() => toFiniteNumber(props.card.outstanding_balance, 0))

const utilizationRaw = computed(() => {
  if (!hasLimit.value) return null
  return (outstandingBalanceValue.value / props.card.credit_limit!) * 100
})

const utilizationPercent = computed(() => {
  if (utilizationRaw.value === null) return 0
  return utilizationRaw.value
})

const utilizationDisplay = computed(() => {
  if (utilizationRaw.value === null) return 'N/A'
  return `${utilizationRaw.value.toFixed(1)}%`
})

const utilizationClamped = computed(() => {
  return Math.max(0, Math.min(100, utilizationPercent.value))
})

const utilizationTone = computed(() => {
  if (!hasLimit.value) return 'tone-neutral'
  if (utilizationPercent.value >= 75) return 'tone-high'
  if (utilizationPercent.value >= 50) return 'tone-medium'
  return 'tone-low'
})

const currentBalanceDisplay = computed(() => formatAmount(currentBalanceValue.value))

const outstandingBalanceDisplay = computed(() => formatAmount(outstandingBalanceValue.value))

const limitDisplay = computed(() => {
  if (!hasLimit.value) return 'Not set'
  return formatAmount(props.card.credit_limit!)
})

const brandLabel = computed(() => {
  const labels: Record<string, string> = {
    visa: 'VISA',
    mastercard: 'Mastercard',
    amex: 'AMEX',
    discover: 'Discover',
  }

  return labels[props.card.brand] ?? 'Card'
})

const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const normalized = hex.replace('#', '').trim()
  const isShort = normalized.length === 3
  const fullHex = isShort
    ? normalized
        .split('')
        .map((chunk) => `${chunk}${chunk}`)
        .join('')
    : normalized

  if (!/^[0-9a-fA-F]{6}$/.test(fullHex)) {
    return null
  }

  return {
    r: parseInt(fullHex.slice(0, 2), 16),
    g: parseInt(fullHex.slice(2, 4), 16),
    b: parseInt(fullHex.slice(4, 6), 16),
  }
}

const cardSurfaceStyle = computed<Record<string, string>>(() => {
  const accent = getCardBackgroundColor(props.card.bank)
  const rgb = hexToRgb(accent)

  if (!rgb) {
    return {
      '--card-accent': '#6B7280',
      '--card-accent-strong': 'rgba(107, 114, 128, 0.55)',
      '--card-accent-soft': 'rgba(107, 114, 128, 0.4)',
      '--card-accent-faint': 'rgba(107, 114, 128, 0.2)',
      '--card-accent-border': 'rgba(107, 114, 128, 0.5)',
    }
  }

  return {
    '--card-accent': accent,
    '--card-accent-strong': `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.55)`,
    '--card-accent-soft': `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.4)`,
    '--card-accent-faint': `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.2)`,
    '--card-accent-border': `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.5)`,
  }
})

const handleSetLimit = () => {
  emit('set-limit', props.card)
}
</script>

<template>
  <article class="credit-card-tile" :style="cardSurfaceStyle" :aria-label="`${card.bank} card ending in ${card.last4}`">
    <div class="card-decoration card-decoration--top" aria-hidden="true"></div>
    <div class="card-decoration card-decoration--bottom" aria-hidden="true"></div>

    <header class="card-top-row">
      <div class="issuer-copy">
        <p class="issuer-name">{{ card.bank }}</p>
        <p class="issuer-subtitle">Credit card</p>
      </div>

      <div class="brand-logo" :class="`brand-logo--${card.brand}`" :aria-label="brandLabel">
        <template v-if="card.brand === 'mastercard'">
          <span class="master-dot master-dot--left" aria-hidden="true"></span>
          <span class="master-dot master-dot--right" aria-hidden="true"></span>
        </template>
        <template v-else>
          <span class="brand-word">{{ brandLabel }}</span>
        </template>
      </div>
    </header>

    <section class="card-middle-row">
      <p class="masked-number">
        <span v-for="group in 3" :key="group" class="dot-group" aria-hidden="true">
          <span v-for="dot in 4" :key="`${group}-${dot}`" class="dot"></span>
        </span>
        <span class="last-four">{{ card.last4 }}</span>
      </p>
    </section>

    <section class="card-bottom-row">
      <div class="utilization-head">
        <span class="utilization-label">Utilization</span>
        <span class="utilization-value" :class="utilizationTone" data-testid="utilization">
          {{ utilizationDisplay }}
        </span>
      </div>

      <div class="utilization-track" data-testid="progress-bar">
        <div
          class="utilization-fill"
          :class="utilizationTone"
          :style="{ width: `${utilizationClamped}%` }"
          role="progressbar"
          :aria-valuenow="utilizationRaw === null ? 0 : utilizationPercent"
          aria-valuemin="0"
          aria-valuemax="100"
          :aria-label="`Card utilization ${utilizationDisplay}`"
        ></div>
      </div>

      <div class="stats-row">
        <div class="stat-item">
          <span class="stat-label">Balance</span>
          <span class="stat-value">{{ currentBalanceDisplay }}</span>
        </div>

        <div class="stat-item stat-item--center">
          <span class="stat-label">Outstanding</span>
          <span class="stat-value" data-testid="outstanding-balance">{{ outstandingBalanceDisplay }}</span>
        </div>

        <div class="stat-item stat-item--end">
          <span class="stat-label">Limit</span>
          <span class="stat-value" data-testid="credit-limit">{{ limitDisplay }}</span>
        </div>
      </div>

      <button
        v-if="!hasLimit"
        type="button"
        class="set-limit-button"
        @click="handleSetLimit"
        data-testid="set-limit-button"
      >
        Set credit limit
      </button>
    </section>
  </article>
</template>

<style scoped>
.credit-card-tile {
  --card-accent: #6b7280;
  --card-accent-strong: rgba(107, 114, 128, 0.55);
  --card-accent-soft: rgba(107, 114, 128, 0.4);
  --card-accent-faint: rgba(107, 114, 128, 0.2);
  --card-accent-border: rgba(107, 114, 128, 0.5);

  position: relative;
  overflow: hidden;
  border-radius: 20px;
  padding: 20px;
  color: #f8fafc;
  aspect-ratio: 1.586 / 1;
  min-height: 250px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background:
    linear-gradient(118deg, var(--card-accent-strong) -20%, transparent 46%),
    linear-gradient(12deg, transparent 60%, var(--card-accent-faint) 100%),
    radial-gradient(circle at 90% -10%, var(--card-accent-soft), transparent 45%),
    radial-gradient(circle at 0% 115%, var(--card-accent-faint), transparent 42%),
    linear-gradient(148deg, #1f2937 0%, #111827 44%, #030712 100%);
  border: 1px solid var(--card-accent-border);
  box-shadow:
    0 18px 30px rgba(2, 6, 23, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.card-decoration {
  position: absolute;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  pointer-events: none;
}

.card-decoration--top {
  width: 180px;
  height: 180px;
  top: -96px;
  right: -72px;
}

.card-decoration--bottom {
  width: 220px;
  height: 220px;
  left: -118px;
  bottom: -140px;
}

.card-top-row,
.card-middle-row,
.card-bottom-row {
  position: relative;
  z-index: 1;
}

.card-top-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.issuer-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.issuer-name {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: rgba(255, 255, 255, 0.88);
}

.issuer-subtitle {
  margin: 0;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.5);
}

.brand-logo {
  min-height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.92);
}

.brand-word {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.master-dot {
  width: 20px;
  height: 20px;
  border-radius: 999px;
}

.master-dot--left {
  background: rgba(220, 38, 38, 0.9);
}

.master-dot--right {
  background: rgba(245, 158, 11, 0.9);
  margin-left: -8px;
}

.card-middle-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.masked-number {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  letter-spacing: 0.12em;
  font-weight: 600;
  font-family: 'JetBrains Mono', 'SFMono-Regular', Menlo, Consolas, monospace;
}

.dot-group {
  display: inline-flex;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(248, 250, 252, 0.5);
}

.last-four {
  letter-spacing: 0.18em;
}

.card-bottom-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.utilization-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.utilization-label,
.stat-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: rgba(255, 255, 255, 0.58);
}

.utilization-value {
  font-size: 12px;
  font-weight: 700;
}

.utilization-track {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.16);
}

.utilization-fill {
  height: 100%;
  transition: width 220ms ease;
}

.tone-low {
  color: #86efac;
}

.tone-medium {
  color: #fcd34d;
}

.tone-high {
  color: #fca5a5;
}

.tone-neutral {
  color: rgba(226, 232, 240, 0.85);
}

.utilization-fill.tone-low {
  background: linear-gradient(90deg, #4ade80, #22c55e);
}

.utilization-fill.tone-medium {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.utilization-fill.tone-high {
  background: linear-gradient(90deg, #ef4444, #f97316);
}

.utilization-fill.tone-neutral {
  background: rgba(226, 232, 240, 0.55);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-item--center {
  text-align: center;
}

.stat-item--end {
  text-align: right;
}

.stat-value {
  font-size: 13px;
  font-weight: 700;
  color: rgba(248, 250, 252, 0.95);
}

.set-limit-button {
  width: 100%;
  margin-top: 4px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.1);
  color: #f8fafc;
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background-color 160ms ease,
    border-color 160ms ease;
}

.set-limit-button:hover {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.65);
}

.set-limit-button:focus-visible {
  outline: 2px solid rgba(248, 250, 252, 0.9);
  outline-offset: 1px;
}

@media (max-width: 768px) {
  .credit-card-tile {
    padding: 18px;
    min-height: 230px;
  }

  .masked-number {
    font-size: 15px;
    gap: 9px;
  }

  .stat-value {
    font-size: 12px;
  }
}
</style>
