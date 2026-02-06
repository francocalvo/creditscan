<script setup lang="ts">
interface Props {
  title: string
  value: string
  change?: string
  changeType?: 'positive' | 'negative' | 'neutral'
  icon?: string
  subtitle?: string
}

defineProps<Props>()
</script>

<template>
  <div class="metric-card">
    <div class="metric-header">
      <span class="metric-title">{{ title }}</span>
      <i v-if="icon" :class="['metric-icon', icon]"></i>
    </div>

    <div class="metric-value">{{ value }}</div>

    <div v-if="change || subtitle" class="metric-footer">
      <span v-if="change" :class="['metric-change', `change-${changeType}`]">
        {{ change }}
      </span>
      <span v-if="subtitle" class="metric-subtitle">
        {{ subtitle }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.metric-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 24px;
  transition: box-shadow 0.2s;
}

.metric-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.metric-title {
  font-size: 14px;
  color: var(--text-muted);
  font-weight: 500;
}

.metric-icon {
  font-size: 18px;
  color: var(--text-placeholder);
}

.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-heading);
  margin-bottom: 8px;
}

.metric-footer {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-change {
  font-size: 13px;
  font-weight: 500;
}

.change-positive {
  color: var(--status-positive);
}

.change-negative {
  color: var(--status-negative);
}

.change-neutral {
  color: var(--text-muted);
}

.metric-subtitle {
  font-size: 13px;
  color: var(--text-muted);
}
</style>
