<script setup lang="ts">
 import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
 import { useRouter } from 'vue-router'
 import { useToast } from 'primevue/usetoast'
 import type { ToastMessageOptions } from 'primevue/toast'
 import Dialog from 'primevue/dialog'
 import Dropdown from 'primevue/dropdown'
 import Button from 'primevue/button'
 import ProgressSpinner from 'primevue/progressspinner'
 import Message from 'primevue/message'
 import { useCreditCards } from '@/composables/useCreditCards'
 import { useStatementUpload } from '@/composables/useStatementUpload'
 import FileDropZone from '@/components/FileDropZone.vue'

// PrimeVue type definitions don't include 'data' property, but it's supported at runtime
interface ExtendedToastMessageOptions extends ToastMessageOptions {
  data?: { statementId?: string }
}

 interface Props {
   visible: boolean
 }

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'upload-complete', statementId: string): void
}

type ModalStep = 'select-card' | 'upload-file' | 'processing' | 'success' | 'error'

const props = defineProps<Props>()
 const emit = defineEmits<Emits>()
const router = useRouter()
 const toast = useToast()

// Step management
const currentStep = ref<ModalStep>('select-card')
const selectedCardId = ref<string | null>(null)

// File selection state
const selectedFile = ref<File | null>(null)
const validationError = ref<string | null>(null)

// Card data from existing composable
const { cards, isLoading: isLoadingCards, fetchCards } = useCreditCards()

// Upload state from composable
const {
  isUploading,
  jobId,
  jobStatus,
  errorMessage: uploadErrorMessage,
  statementId,
  duplicateJobId,
  uploadStatement,
  pollJobStatus,
  startBackgroundPolling,
  stopPolling,
  reset: resetUpload,
} = useStatementUpload()

/**
 * Update modal visibility, ensuring close actions run through one path.
 * When closing during processing, switches polling to the background completion handler.
 */
function setVisible(value: boolean): void {
  if (!value && props.visible && currentStep.value === 'processing' && jobId.value) {
    startBackgroundPolling(jobId.value, handleBackgroundComplete)
  }
  emit('update:visible', value)
}

// Internal visible state that syncs with prop
const internalVisible = computed({
  get: () => props.visible,
  set: setVisible
})

// Dropdown options computed from cards
const cardOptions = computed(() =>
  cards.value.map((card) => ({
    label: `${card.bank} - ${card.brand} ****${card.last4}`,
    value: card.id
  }))
)

// Check if Next button should be disabled
const isNextDisabled = computed(() => selectedCardId.value === null)

/**
 * Determine if modal can be closed.
 * This modal should remain dismissible (X button + backdrop) during processing.
 */
const canClose = computed(() => true)

/**
 * Processing status message based on job status.
 */
const processingStatusMessage = computed(() => {
  if (jobStatus.value === 'pending') {
    return 'Waiting to process...'
  } else if (jobStatus.value === 'processing') {
    return 'Extracting data from PDF...'
  } else if (jobStatus.value === 'failed') {
    return uploadErrorMessage.value || 'Processing failed'
  }
  return 'Processing...'
})

/**
 * Close modal. Starts background polling if closing during processing.
 */
function closeModal(): void {
  setVisible(false)
}

/**
 * Handle background job completion with toast notification.
 * Only shows toast when modal is closed to avoid duplicate notifications.
 */
function handleBackgroundComplete(job: {
  status: string
  statement_id: string | null
  error_message: string | null
}): void {
  // Only show toast if modal is actually closed (user didn't just open it again)
  if (props.visible) {
    return
  }

  if (job.status === 'completed' || job.status === 'partial') {
    toast.add({
      severity: job.status === 'completed' ? 'success' : 'warn',
      summary: 'Statement Uploaded',
      detail:
        job.status === 'partial'
          ? 'Statement imported with partial data'
          : 'Your statement is ready to view',
      life: 5000,
      group: 'upload-complete',
      data: { statementId: job.statement_id }
    } as ExtendedToastMessageOptions)
  } else if (job.status === 'failed') {
    toast.add({
      severity: 'error',
      summary: 'Upload Failed',
      detail: job.error_message || 'Failed to process statement',
      life: 8000,
      group: 'upload-complete'
    })
  }
}

/**
 * Navigate to the upload file step.
 */
function goToUploadStep(): void {
  currentStep.value = 'upload-file'
  validationError.value = null
}

/**
 * Navigate back to the card selection step.
 */
function goToCardSelection(): void {
  currentStep.value = 'select-card'
  validationError.value = null
}

/**
 * Handle file validation errors from FileDropZone.
 */
function handleValidationError(message: string): void {
  validationError.value = message
}

/**
 * Handle file selection change - clear validation error on valid selection.
 */
function handleFileChange(file: File | null): void {
  selectedFile.value = file
  if (file) {
    validationError.value = null
  }
}

/**
 * Handle upload button click - uploads file and starts polling.
 */
async function handleUpload(): Promise<void> {
  if (!selectedCardId.value || !selectedFile.value) {
    return
  }

  // Transition to processing step immediately
  currentStep.value = 'processing'
  validationError.value = null

  try {
    const job = await uploadStatement(selectedCardId.value, selectedFile.value)

    // Start polling for job status updates.
    // If the user already closed the modal while the upload request was in-flight,
    // keep polling in the background and notify via toast on completion.
    startBackgroundPolling(job.id, props.visible ? handleJobComplete : handleBackgroundComplete)
  } catch (error) {
    // Detect network errors (TypeError from fetch usually indicates network failure)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      uploadErrorMessage.value = 'Network error. Please check your connection and try again.'
    } else if (duplicateJobId.value) {
      // Duplicate already handled by composable
      uploadErrorMessage.value = uploadErrorMessage.value || 'This file was already uploaded.'
    } else {
      // Use existing error message from composable for non-network errors
      uploadErrorMessage.value = uploadErrorMessage.value || 'Upload failed'
    }
    // Transition to error step to show the user something went wrong
    currentStep.value = 'error'
  }
}

/**
 * Handle job completion from background polling.
 */
function handleJobComplete(job: { status: string; statement_id: string | null }): void {
  if (job.status === 'completed' || job.status === 'partial') {
    // Transition to success step
    currentStep.value = 'success'
  } else if (job.status === 'failed') {
    // Transition to error step
    currentStep.value = 'error'
  }
}

/**
 * Navigate to the cards page and close modal.
 */
function navigateToCards(): void {
  closeModal()
  router.push('/cards')
}

/**
 * Reset modal state when it opens.
 */
function resetModal(): void {
  currentStep.value = 'select-card'
  selectedCardId.value = null
  selectedFile.value = null
  validationError.value = null
  resetUpload()
}

/**
 * Emit upload completion and close the modal.
 */
function viewStatement(): void {
  if (!statementId.value) {
    return
  }

  emit('upload-complete', statementId.value)
  closeModal()
}

/**
 * View existing duplicate statement.
 * Fetches job details for the duplicate job ID and navigates to it.
 */
async function viewDuplicateStatement(): Promise<void> {
  if (!duplicateJobId.value) {
    return
  }

  try {
    const job = await pollJobStatus(duplicateJobId.value)
    if (job.statement_id) {
      // Job is complete, navigate to the statement
      emit('upload-complete', job.statement_id)
      closeModal()
    } else {
      // Job is still processing, show feedback
      if (job.status === 'processing' || job.status === 'pending') {
        uploadErrorMessage.value = 'The duplicate statement is still being processed. Please try again in a few moments.'
      } else {
        uploadErrorMessage.value = 'Unable to view the existing statement'
      }
    }
  } catch {
    // If we can't fetch the duplicate job, update error message
    uploadErrorMessage.value = 'Unable to retrieve existing statement'
  }
}

/**
 * Retry upload after error - clears file and returns to upload step.
 */
function retryUpload(): void {
  selectedFile.value = null
  goToUploadStep()
}

// Watch for job status changes to transition steps (when modal is open and in processing step)
watch(
  jobStatus,
  (newStatus) => {
    if (!props.visible || currentStep.value !== 'processing') {
      return
    }

    if (newStatus === 'completed' || newStatus === 'partial') {
      currentStep.value = 'success'
    } else if (newStatus === 'failed') {
      currentStep.value = 'error'
    }
  }
)

// Fetch cards when modal becomes visible
watch(
  () => props.visible,
  (newValue) => {
    if (newValue) {
      resetModal()
      fetchCards()
    }
  }
)

// Also fetch cards on mount if already visible
onMounted(() => {
  if (props.visible) {
    fetchCards()
  }
})

// Cleanup polling on unmount
onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <Dialog
    v-model:visible="internalVisible"
    modal
    header="Upload Statement"
    :style="{ width: '500px' }"
    :closable="canClose"
    :dismissableMask="canClose"
    :draggable="false"
  >
    <div class="upload-modal-content">
      <!-- Loading state -->
      <div v-if="isLoadingCards" class="loading-state">
        <ProgressSpinner />
        <p>Loading cards...</p>
      </div>

      <!-- No cards state -->
      <div v-else-if="cards.length === 0" class="empty-state">
        <i class="pi pi-credit-card empty-state__icon"></i>
        <p class="empty-state__text">No cards found. Add a card first.</p>
        <Button
          label="Go to Cards"
          icon="pi pi-arrow-right"
          @click="navigateToCards"
        />
      </div>

      <!-- Card selection (Step 1) -->
      <div v-else-if="currentStep === 'select-card'" class="card-selection">
        <div class="form-field">
          <label for="card-select" class="field-label">Select a credit card</label>
          <Dropdown
            id="card-select"
            v-model="selectedCardId"
            :options="cardOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Choose a card"
            class="w-full"
          />
        </div>

        <div class="button-group">
          <Button
            label="Cancel"
            severity="secondary"
            outlined
            @click="closeModal"
          />
          <Button
            label="Next"
            icon="pi pi-arrow-right"
            iconPos="right"
            :disabled="isNextDisabled"
            @click="goToUploadStep"
          />
        </div>
      </div>

      <!-- Upload file step -->
      <div v-else-if="currentStep === 'upload-file'" class="upload-step">
        <FileDropZone
          :model-value="selectedFile"
          accept=".pdf"
          :max-size="25 * 1024 * 1024"
          @update:model-value="handleFileChange"
          @validation-error="handleValidationError"
        />

        <Message v-if="validationError" severity="error" :closable="false">
          {{ validationError }}
        </Message>

        <div class="button-group">
          <Button
            label="Back"
            severity="secondary"
            outlined
            @click="goToCardSelection"
          />
          <Button
            label="Upload"
            icon="pi pi-upload"
            :loading="isUploading"
            :disabled="!selectedFile"
            @click="handleUpload"
          />
        </div>
      </div>

      <!-- Processing step -->
      <div v-else-if="currentStep === 'processing'" class="processing-step">
        <ProgressSpinner class="processing-spinner" />
        <div class="processing-content">
          <p class="processing-message">{{ processingStatusMessage }}</p>
          <p class="processing-hint">
            You can close this modal. We'll notify you when it's done.
          </p>
        </div>
      </div>

      <!-- Success step (placeholder - implemented in Step 6) -->
      <div v-else-if="currentStep === 'success'" class="success-step">
        <div class="success-message">
          <i class="pi pi-check-circle success-icon" aria-hidden="true"></i>
          <h3 class="success-title">Statement Uploaded</h3>

          <Message v-if="jobStatus === 'partial'" severity="warn" :closable="false">
            Statement imported with partial data. Please review.
          </Message>
        </div>

        <div class="button-group button-group--center">
          <Button label="Upload Another" text @click="resetModal" />
          <Button label="View Statement" :disabled="!statementId" @click="viewStatement" />
        </div>
      </div>

      <!-- Error step -->
      <div v-else-if="currentStep === 'error'" class="error-step">
        <div class="error-message">
          <i class="pi pi-times-circle error-icon" aria-hidden="true"></i>
          <h3 class="error-title">Upload Failed</h3>
          <p class="error-text">{{ uploadErrorMessage || 'An error occurred while uploading' }}</p>

          <div v-if="duplicateJobId" class="duplicate-link">
            <p>This file was already uploaded.</p>
            <Button
              label="View Existing Statement"
              link
              @click="viewDuplicateStatement"
            />
          </div>
        </div>

        <div class="button-group button-group--center">
          <Button label="Try Again" @click="retryUpload" />
        </div>
      </div>
    </div>
  </Dialog>
</template>

<style scoped>
.upload-modal-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 0.5rem 0;
  min-height: 150px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 2rem;
}

.loading-state p {
  margin: 0;
  color: var(--text-color-secondary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 2rem;
  text-align: center;
}

.empty-state__icon {
  font-size: 3rem;
  color: var(--text-color-secondary);
}

.empty-state__text {
  margin: 0;
  font-size: 1rem;
  color: var(--text-color);
}

.card-selection {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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

.button-group {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.button-group--center {
  justify-content: center;
}

.w-full {
  width: 100%;
}

.upload-step,
.processing-step,
.success-step,
.error-step {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.processing-step {
  align-items: center;
  text-align: center;
  padding: 1rem 0;
}

.processing-spinner {
  width: 50px;
  height: 50px;
  margin-bottom: 1rem;
}

.processing-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.processing-message {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.processing-hint {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
  margin: 0;
}

.success-message {
  text-align: center;
  padding: 1.5rem 0.5rem;
}

.success-icon {
  font-size: 3rem;
  color: #10b981;
}

.success-title {
  margin: 1rem 0 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.error-message {
  text-align: center;
  padding: 1.5rem 0.5rem;
}

.error-icon {
  font-size: 3rem;
  color: #ef4444;
}

.error-title {
  margin: 1rem 0 0.5rem;
  font-size: 1.25rem;
  font-weight: 600;
}

.error-text {
  margin: 0.5rem 0;
  color: var(--text-color-secondary);
}

.duplicate-link {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.duplicate-link p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}
</style>
