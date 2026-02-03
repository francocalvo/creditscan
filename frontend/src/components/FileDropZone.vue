<script setup lang="ts">
import { ref, type Ref } from 'vue'
import Button from 'primevue/button'

interface Props {
  modelValue: File | null
  accept: string
  maxSize: number
  disabled?: boolean
}

interface Emits {
  (e: 'update:modelValue', file: File | null): void
  (e: 'validation-error', message: string): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})
const emit = defineEmits<Emits>()

const isDragging = ref(false)
const fileInput: Ref<HTMLInputElement | null> = ref(null)

/**
 * Parse accepted extensions from the accept prop.
 * Returns lowercase extensions with leading dots.
 */
function parseAcceptedExtensions(): string[] {
  return props.accept
    .split(',')
    .map((ext) => ext.trim().toLowerCase())
    .filter((ext) => ext.startsWith('.'))
}

/**
 * Validate file extension against accept prop.
 */
function isValidExtension(file: File): boolean {
  const extensions = parseAcceptedExtensions()
  const fileName = file.name.toLowerCase()
  return extensions.some((ext) => fileName.endsWith(ext))
}

/**
 * Validate file size against maxSize prop.
 */
function isValidSize(file: File): boolean {
  return file.size <= props.maxSize
}

/**
 * Compute human-readable size limit from maxSize.
 */
function formatSizeLimit(): string {
  const mb = Math.floor(props.maxSize / (1024 * 1024))
  return `${mb}MB`
}

/**
 * Validate file and emit appropriate event.
 */
function validateAndEmit(file: File): void {
  if (!isValidExtension(file)) {
    emit('validation-error', 'Please select a PDF file')
    return
  }

  if (!isValidSize(file)) {
    emit('validation-error', `File size exceeds ${formatSizeLimit()} limit`)
    return
  }

  emit('update:modelValue', file)
}

/**
 * Handle dragover event.
 */
function onDragOver(event: DragEvent): void {
  event.preventDefault()
  if (props.disabled) return
  isDragging.value = true
}

/**
 * Handle dragleave event.
 */
function onDragLeave(): void {
  if (props.disabled) return
  isDragging.value = false
}

/**
 * Handle drop event.
 */
function onDrop(event: DragEvent): void {
  event.preventDefault()
  isDragging.value = false

  if (props.disabled) return

  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    validateAndEmit(files[0])
  }

  // Reset input value to allow re-selecting same file
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

/**
 * Open the native file picker.
 */
function openFilePicker(): void {
  if (props.disabled) return
  fileInput.value?.click()
}

/**
 * Handle file selection from native picker.
 */
function onFileSelect(event: Event): void {
  const target = event.target as HTMLInputElement
  const files = target.files

  if (files && files.length > 0) {
    validateAndEmit(files[0])
  }

  // Reset input value to allow re-selecting same file
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

/**
 * Clear the selected file.
 */
function clearFile(event: MouseEvent): void {
  event.stopPropagation()
  emit('update:modelValue', null)

  // Reset input value
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}
</script>

<template>
  <div
    class="drop-zone"
    :class="{
      'drop-zone--active': isDragging,
      'drop-zone--disabled': disabled
    }"
    @dragover.prevent="onDragOver"
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
    @click="openFilePicker"
  >
    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      hidden
      @change="onFileSelect"
    />

    <!-- Empty state: prompt -->
    <div v-if="!modelValue" class="drop-zone__prompt">
      <i class="pi pi-upload drop-zone__icon"></i>
      <p class="drop-zone__text">Drag & drop your PDF here</p>
      <p class="drop-zone__subtext">or click to browse</p>
    </div>

    <!-- File selected state -->
    <div v-else class="drop-zone__file">
      <i class="pi pi-file-pdf drop-zone__file-icon"></i>
      <span class="drop-zone__filename">{{ modelValue.name }}</span>
      <Button
        icon="pi pi-times"
        severity="secondary"
        text
        rounded
        aria-label="Clear file"
        class="drop-zone__clear-btn"
        @click="clearFile"
      />
    </div>
  </div>
</template>

<style scoped>
.drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 150px;
  padding: 2rem;
  border: 2px dashed var(--surface-border);
  border-radius: 8px;
  background-color: var(--surface-ground);
  cursor: pointer;
  transition:
    border-color 0.2s,
    background-color 0.2s;
}

.drop-zone:hover {
  border-color: var(--primary-color);
  background-color: var(--surface-50);
}

.drop-zone--active {
  border-color: var(--primary-color);
  background-color: var(--primary-color-alpha-10, rgba(var(--primary-color-rgb), 0.1));
}

.drop-zone--disabled {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
}

.drop-zone__prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  text-align: center;
}

.drop-zone__icon {
  font-size: 2.5rem;
  color: var(--text-color-secondary);
}

.drop-zone__text {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-color);
}

.drop-zone__subtext {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

.drop-zone__file {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  background-color: var(--surface-card);
  border-radius: 6px;
  border: 1px solid var(--surface-border);
}

.drop-zone__file-icon {
  font-size: 1.5rem;
  color: var(--red-500);
}

.drop-zone__filename {
  font-size: 0.938rem;
  color: var(--text-color);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drop-zone__clear-btn {
  flex-shrink: 0;
}
</style>
