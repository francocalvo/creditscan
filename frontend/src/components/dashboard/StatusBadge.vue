<script setup lang="ts">
interface Props {
  status: 'paid' | 'pending' | 'overdue'
  label?: string
}

const props = defineProps<Props>()

const statusLabels: Record<string, string> = {
  paid: 'paid',
  pending: 'pending',
  overdue: 'overdue'
}

const statusIcons: Record<string, string> = {
  paid: 'pi pi-check',
  pending: 'pi pi-clock',
  overdue: 'pi pi-exclamation-triangle'
}

const displayLabel = props.label || statusLabels[props.status]
const iconClass = statusIcons[props.status]
</script>

<template>
  <span :class="['status-badge', `status-${status}`]">
    <i :class="['status-icon', iconClass]"></i>
    {{ displayLabel }}
  </span>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.status-icon {
  font-size: 11px;
}

.status-paid {
  background-color: #d1fae5;
  color: #065f46;
}

.status-pending {
  background-color: #fef3c7;
  color: #92400e;
}

.status-overdue {
  background-color: #fee2e2;
  color: #991b1b;
}
</style>

