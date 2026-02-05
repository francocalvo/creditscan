<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useTags, type Tag } from '@/composables/useTags'

interface Props {
  visible: boolean
  tag: Tag | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'saved'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { createTag, updateTag } = useTags()

const COLOR_PALETTE = [
  '#EF4444', // Red
  '#F97316', // Orange
  '#EAB308', // Yellow
  '#22C55E', // Green
  '#14B8A6', // Teal
  '#3B82F6', // Blue
  '#8B5CF6', // Violet
  '#EC4899', // Pink
  '#6B7280', // Gray
  '#78716C', // Stone
  '#0EA5E9', // Sky
  '#A855F7', // Purple
]

// Form state
const label = ref('')
const selectedColor = ref(COLOR_PALETTE[0])

// UX state
const formSubmitted = ref(false)
const isSaving = ref(false)
const serverError = ref<string | null>(null)

/**
 * Whether modal is in edit mode (tag prop is provided)
 */
const isEditMode = computed(() => props.tag !== null)

/**
 * Dialog header text
 */
const dialogHeader = computed(() => (isEditMode.value ? 'Edit Tag' : 'Create Tag'))

/**
 * Save button label
 */
const saveButtonLabel = computed(() => (isEditMode.value ? 'Save' : 'Create'))

/**
 * Label validation error
 */
const labelError = computed((): string | null => {
  if (!formSubmitted.value) return null
  const trimmed = label.value.trim()
  if (!trimmed) {
    return 'Label is required'
  }
  if (trimmed.length > 50) {
    return 'Label must be 50 characters or less'
  }
  return null
})

/**
 * Form validity
 */
const isFormValid = computed(() => !labelError.value)

/**
 * Reset form to initial state
 */
function resetForm(): void {
  label.value = ''
  selectedColor.value = COLOR_PALETTE[0]
  formSubmitted.value = false
  serverError.value = null
  isSaving.value = false
}

/**
 * Populate form with tag data for editing
 */
function populateForm(tag: Tag): void {
  label.value = tag.label
  selectedColor.value = tag.color || COLOR_PALETTE[0]
}

/**
 * Watch for visibility changes to reset/populate form
 */
watch(
  () => props.visible,
  (newVisible) => {
    if (newVisible) {
      resetForm()
      if (props.tag) {
        populateForm(props.tag)
      }
    }
  }
)

/**
 * Update modal visibility
 */
function setVisible(value: boolean): void {
  emit('update:visible', value)
}

// Internal visible state that syncs with prop
const internalVisible = computed({
  get: () => props.visible,
  set: setVisible,
})

/**
 * Handle save button click
 */
async function handleSave(): Promise<void> {
  formSubmitted.value = true
  serverError.value = null

  if (!isFormValid.value) {
    return
  }

  isSaving.value = true

  try {
    if (isEditMode.value && props.tag) {
      await updateTag(props.tag.tag_id, {
        label: label.value.trim(),
        color: selectedColor.value,
      })
    } else {
      await createTag({
        label: label.value.trim(),
        color: selectedColor.value,
      })
    }

    emit('saved')
    setVisible(false)
  } catch (e) {
    serverError.value = e instanceof Error ? e.message : 'Failed to save tag'
  } finally {
    isSaving.value = false
  }
}

/**
 * Handle cancel button click
 */
function handleCancel(): void {
  setVisible(false)
}

/**
 * Select a color from the palette
 */
function selectColor(color: string): void {
  selectedColor.value = color
}
</script>

<template>
  <Dialog
    v-model:visible="internalVisible"
    modal
    :header="dialogHeader"
    :style="{ width: '400px' }"
    :breakpoints="{ '640px': '90vw' }"
    :closable="!isSaving"
    :dismissableMask="!isSaving"
    :draggable="false"
  >
    <div class="tag-form">
      <!-- Server Error Message -->
      <Message v-if="serverError" severity="error" :closable="false" class="server-error">
        {{ serverError }}
      </Message>

      <!-- Label Field -->
      <div class="form-field">
        <label for="tag-label-input" class="field-label">Label</label>
        <InputText
          id="tag-label-input"
          v-model="label"
          :disabled="isSaving"
          :class="{ 'p-invalid': !!labelError }"
          placeholder="e.g., Groceries, Entertainment"
          class="w-full"
          maxlength="50"
        />
        <small v-if="labelError" class="p-error">{{ labelError }}</small>
      </div>

      <!-- Color Palette -->
      <div class="form-field">
        <label class="field-label">Color</label>
        <div class="color-palette">
          <button
            v-for="color in COLOR_PALETTE"
            :key="color"
            type="button"
            class="color-swatch"
            :class="{ 'color-swatch--selected': selectedColor === color }"
            :style="{ backgroundColor: color }"
            :disabled="isSaving"
            :aria-label="`Select color ${color}`"
            :aria-pressed="selectedColor === color"
            @click="selectColor(color)"
          >
            <i v-if="selectedColor === color" class="pi pi-check"></i>
          </button>
        </div>
      </div>

      <!-- Preview -->
      <div class="form-field">
        <label class="field-label">Preview</label>
        <div class="tag-preview">
          <span class="tag-chip" :style="{ backgroundColor: selectedColor }">
            {{ label.trim() || 'Tag Label' }}
          </span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="modal-footer">
        <Button
          label="Cancel"
          severity="secondary"
          outlined
          :disabled="isSaving"
          @click="handleCancel"
        />
        <Button
          :label="saveButtonLabel"
          icon="pi pi-check"
          :loading="isSaving"
          :disabled="isSaving"
          @click="handleSave"
        />
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
.tag-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.server-error {
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

.color-palette {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0.5rem;
}

.color-swatch {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 2px solid transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.color-swatch:hover:not(:disabled) {
  transform: scale(1.1);
}

.color-swatch:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.color-swatch--selected {
  border-color: #111827;
}

.color-swatch i {
  color: white;
  font-size: 0.875rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.tag-preview {
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 8px;
  display: flex;
  align-items: center;
}

.tag-chip {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
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
