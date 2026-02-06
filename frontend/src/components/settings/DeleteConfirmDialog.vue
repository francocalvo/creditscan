<script setup lang="ts">
import { computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Message from 'primevue/message'

interface Props {
  visible: boolean
  title: string
  message: string
  warningMessage?: string
  loading?: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'confirm'): void
}

const props = withDefaults(defineProps<Props>(), {
  warningMessage: undefined,
  loading: false,
})
const emit = defineEmits<Emits>()

/**
 * Update modal visibility
 */
function setVisible(value: boolean): void {
  if (!props.loading) {
    emit('update:visible', value)
  }
}

// Internal visible state that syncs with prop
const internalVisible = computed({
  get: () => props.visible,
  set: setVisible,
})

/**
 * Handle cancel button click
 */
function handleCancel(): void {
  setVisible(false)
}

/**
 * Handle delete button click
 */
function handleConfirm(): void {
  emit('confirm')
}
</script>

<template>
  <Dialog
    v-model:visible="internalVisible"
    modal
    :header="title"
    :style="{ width: '400px' }"
    :breakpoints="{ '640px': '90vw' }"
    :closable="!loading"
    :dismissableMask="!loading"
    :draggable="false"
  >
    <div class="delete-dialog-content">
      <p class="delete-message">{{ message }}</p>

      <Message v-if="warningMessage" severity="warn" :closable="false" class="warning-message">
        {{ warningMessage }}
      </Message>
    </div>

    <template #footer>
      <div class="modal-footer">
        <Button
          label="Cancel"
          severity="secondary"
          outlined
          :disabled="loading"
          @click="handleCancel"
        />
        <Button
          label="Delete"
          severity="danger"
          icon="pi pi-trash"
          :loading="loading"
          :disabled="loading"
          @click="handleConfirm"
        />
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
.delete-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.delete-message {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--text-color);
  line-height: 1.5;
}

.warning-message {
  margin: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}
</style>
