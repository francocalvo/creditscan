<script setup lang="ts">
/**
 * AddCardPlaceholder Component
 *
 * A clickable placeholder tile that appears first in the cards grid.
 * Emits a `click` event to open the card creation flow.
 */

// Define emit for click event
const emit = defineEmits<{
  click: []
}>()

// Handle click event
const handleClick = () => {
  emit('click')
}
</script>

<template>
  <button
    type="button"
    class="add-card-placeholder"
    aria-label="Add new card"
    @click="handleClick"
  >
    <div class="placeholder-content">
      <i class="pi pi-plus placeholder-icon" aria-hidden="true"></i>
      <span class="placeholder-text">Add Card</span>
    </div>
  </button>
</template>

<style scoped>
.add-card-placeholder {
  min-width: 340px;
  min-height: 240px;
  background: #f9fafb;
  border: 2px dashed #d1d5db;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition:
    transform 0.2s,
    border-color 0.2s,
    background-color 0.2s,
    box-shadow 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  outline: none;
}

.add-card-placeholder:hover {
  transform: translateY(-4px);
  border-color: #9ca3af;
  background: #f3f4f6;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.add-card-placeholder:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.placeholder-icon {
  font-size: 48px;
  color: #9ca3af;
}

.placeholder-text {
  font-size: 16px;
  font-weight: 600;
  color: #6b7280;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .add-card-placeholder {
    background: #1f2937;
    border-color: #4b5563;
  }

  .add-card-placeholder:hover {
    background: #374151;
    border-color: #6b7280;
  }

  .add-card-placeholder:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  }

  .placeholder-icon {
    color: #6b7280;
  }

  .placeholder-text {
    color: #9ca3af;
  }
}
</style>
