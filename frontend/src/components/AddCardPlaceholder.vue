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
  width: 100%;
  min-height: 250px;
  aspect-ratio: 1.586 / 1;
  background:
    radial-gradient(circle at 94% -6%, rgba(148, 163, 184, 0.2), transparent 42%),
    radial-gradient(circle at -8% 108%, rgba(51, 65, 85, 0.24), transparent 45%),
    linear-gradient(160deg, #0f172a 0%, #111827 46%, #020617 100%);
  border: 1px dashed rgba(226, 232, 240, 0.45);
  border-radius: 20px;
  padding: 20px;
  cursor: pointer;
  transition:
    transform 0.22s ease,
    border-color 0.22s ease,
    box-shadow 0.22s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  outline: none;
  box-shadow:
    0 18px 30px rgba(2, 6, 23, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.add-card-placeholder:hover {
  transform: translateY(-3px);
  border-color: rgba(241, 245, 249, 0.75);
  box-shadow:
    0 24px 36px rgba(2, 6, 23, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.add-card-placeholder:focus-visible {
  border-color: rgba(241, 245, 249, 0.8);
  box-shadow:
    0 0 0 2px rgba(248, 250, 252, 0.85),
    0 20px 28px rgba(2, 6, 23, 0.26);
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.placeholder-icon {
  font-size: 42px;
  color: rgba(226, 232, 240, 0.85);
}

.placeholder-text {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: rgba(226, 232, 240, 0.9);
}

@media (max-width: 768px) {
  .add-card-placeholder {
    min-height: 230px;
  }
}
</style>
