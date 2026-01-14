<script setup lang="ts">
interface Tab {
  id: string
  label: string
}

interface Props {
  tabs: Tab[]
  activeTab: string
}

interface Emits {
  (e: 'update:activeTab', value: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const handleTabClick = (tabId: string) => {
  emit('update:activeTab', tabId)
}
</script>

<template>
  <div class="tab-navigation">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      :class="['tab-button', { active: activeTab === tab.id }]"
      @click="handleTabClick(tab.id)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<style scoped>
.tab-navigation {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 32px;
}

.tab-button {
  padding: 12px 20px;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-secondary);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  bottom: -1px;
}

.tab-button:hover {
  color: var(--text-primary);
}

.tab-button.active {
  color: var(--text-primary);
  border-bottom-color: var(--text-primary);
}
</style>

