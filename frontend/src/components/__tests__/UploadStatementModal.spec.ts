import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import UploadStatementModal from '../UploadStatementModal.vue'

// Mock vue-router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

// Mock useCreditCards composable
const mockCards = ref<Array<{ id: string; bank: string; brand: string; last4: string }>>([])
const mockIsLoading = ref(false)
const mockFetchCards = vi.fn()

vi.mock('@/composables/useCreditCards', () => ({
  useCreditCards: () => ({
    cards: mockCards,
    isLoading: mockIsLoading,
    fetchCards: mockFetchCards,
    error: ref(null)
  })
}))

// Mock useStatementUpload composable
const mockIsUploading = ref(false)
const mockJobId = ref<string | null>(null)
const mockJobStatus = ref<string | null>(null)
const mockStatementId = ref<string | null>(null)
const mockUploadErrorMessage = ref<string | null>(null)
const mockDuplicateJobId = ref<string | null>(null)
const mockUploadStatement = vi.fn()
const mockPollJobStatus = vi.fn()
const mockStartBackgroundPolling = vi.fn()
const mockStopPolling = vi.fn()
const mockResetUpload = vi.fn()
const mockToastAdd = vi.fn()

vi.mock('@/composables/useStatementUpload', () => ({
  useStatementUpload: () => ({
    isUploading: mockIsUploading,
    jobId: mockJobId,
    jobStatus: mockJobStatus,
    errorMessage: mockUploadErrorMessage,
    statementId: mockStatementId,
    duplicateJobId: mockDuplicateJobId,
    uploadStatement: mockUploadStatement,
    pollJobStatus: mockPollJobStatus,
    startBackgroundPolling: mockStartBackgroundPolling,
    stopPolling: mockStopPolling,
    reset: mockResetUpload,
  })
}))

// Mock useToast
vi.mock('primevue/usetoast', () => ({
  useToast: () => ({
    add: mockToastAdd
  })
}))

// Stub PrimeVue components
const DialogStub = {
  name: 'Dialog',
  template: `
    <div v-if="visible" class="p-dialog">
      <div class="p-dialog-header">
        <span>{{ header }}</span>
        <button v-if="closable" class="p-dialog-header-close" @click="$emit('update:visible', false)">X</button>
      </div>
      <div class="p-dialog-content">
        <slot />
      </div>
    </div>
  `,
  props: ['visible', 'modal', 'header', 'closable', 'draggable'],
  emits: ['update:visible']
}

const DropdownStub = {
  name: 'Dropdown',
  template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option></select>',
  props: ['modelValue', 'options', 'optionLabel', 'optionValue', 'placeholder'],
  emits: ['update:modelValue']
}

const ButtonStub = {
  name: 'Button',
  template: '<button :disabled="disabled || loading" @click="$emit(\'click\', $event)">{{ loading ? \'Loading...\' : label }}</button>',
  props: ['label', 'severity', 'outlined', 'disabled', 'loading', 'icon', 'iconPos', 'text'],
  emits: ['click']
}

const ProgressSpinnerStub = {
  name: 'ProgressSpinner',
  template: '<div class="p-progress-spinner">Loading...</div>'
}

const MessageStub = {
  name: 'Message',
  template: '<div class="p-message" :class="`p-message-${severity}`"><slot /></div>',
  props: ['severity', 'closable']
}

// FileDropZone stub that exposes model value and emits events
const FileDropZoneStub = {
  name: 'FileDropZone',
  template: `
    <div class="file-drop-zone" data-testid="file-drop-zone">
      <span v-if="modelValue">{{ modelValue.name }}</span>
      <span v-else>Drop a file here</span>
    </div>
  `,
  props: ['modelValue', 'accept', 'maxSize'],
  emits: ['update:modelValue', 'validation-error']
}

describe('UploadStatementModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockCards.value = []
    mockIsLoading.value = false
    mockIsUploading.value = false
    mockJobId.value = null
    mockJobStatus.value = null
    mockStatementId.value = null
    mockUploadErrorMessage.value = null
    mockDuplicateJobId.value = null
    // Default mock for uploadStatement to resolve with a job
    mockUploadStatement.mockResolvedValue({
      id: 'job-1',
      status: 'pending',
      statement_id: null,
      error_message: null,
      created_at: '2024-01-01',
      updated_at: null,
      completed_at: null,
    })
    // Default mock for pollJobStatus to resolve with a job
    mockPollJobStatus.mockResolvedValue({
      id: 'job-1',
      status: 'completed',
      statement_id: 'statement-123',
      error_message: null,
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
      completed_at: '2024-01-01',
    })
  })

  function createWrapper(props = {}) {
    return mount(UploadStatementModal, {
      props: { visible: true, ...props },
      global: {
        stubs: {
          Dialog: DialogStub,
          Dropdown: DropdownStub,
          Button: ButtonStub,
          ProgressSpinner: ProgressSpinnerStub,
          Message: MessageStub,
          FileDropZone: FileDropZoneStub
        }
      }
    })
  }

  describe('modal visibility', () => {
    it('modal opens when visible=true', () => {
      const wrapper = createWrapper({ visible: true })

      expect(wrapper.find('.p-dialog').exists()).toBe(true)
    })

    it('modal is hidden when visible=false', () => {
      const wrapper = createWrapper({ visible: false })

      expect(wrapper.find('.p-dialog').exists()).toBe(false)
    })

    it('modal closes when X clicked', async () => {
      const wrapper = createWrapper({ visible: true })

      await wrapper.find('.p-dialog-header-close').trigger('click')

      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(wrapper.emitted('update:visible')![0]).toEqual([false])
    })
  })

  describe('loading state', () => {
    it('shows loading state while fetching cards', () => {
      mockIsLoading.value = true
      const wrapper = createWrapper()

      expect(wrapper.find('.loading-state').exists()).toBe(true)
      expect(wrapper.find('.p-progress-spinner').exists()).toBe(true)
      expect(wrapper.text()).toContain('Loading cards...')
    })

    it('fetches cards on mount when visible', async () => {
      createWrapper({ visible: true })
      await flushPromises()

      expect(mockFetchCards).toHaveBeenCalled()
    })

    it('fetches cards when modal becomes visible', async () => {
      const wrapper = createWrapper({ visible: false })
      mockFetchCards.mockClear()

      await wrapper.setProps({ visible: true })
      await flushPromises()

      expect(mockFetchCards).toHaveBeenCalled()
    })
  })

  describe('empty state', () => {
    it('shows empty state when no cards', () => {
      mockCards.value = []
      const wrapper = createWrapper()

      expect(wrapper.find('.empty-state').exists()).toBe(true)
      expect(wrapper.text()).toContain('No cards found. Add a card first.')
    })

    it('empty state button navigates to cards', async () => {
      mockCards.value = []
      const wrapper = createWrapper()

      const goToCardsButton = wrapper.findAll('button').find((b) => b.text() === 'Go to Cards')
      expect(goToCardsButton).toBeTruthy()

      await goToCardsButton!.trigger('click')

      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(wrapper.emitted('update:visible')![0]).toEqual([false])
      expect(mockPush).toHaveBeenCalledWith('/cards')
    })
  })

  describe('card selection', () => {
    beforeEach(() => {
      mockCards.value = [
        { id: 'card-1', bank: 'Chase', brand: 'visa', last4: '1234' },
        { id: 'card-2', bank: 'Citi', brand: 'mastercard', last4: '5678' }
      ]
    })

    it('shows dropdown when cards exist', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('.card-selection').exists()).toBe(true)
      expect(wrapper.find('select').exists()).toBe(true)
    })

    it('dropdown displays card info correctly', () => {
      const wrapper = createWrapper()

      const options = wrapper.findAll('option')
      expect(options.length).toBe(2)
      expect(options[0].text()).toBe('Chase - visa ****1234')
      expect(options[1].text()).toBe('Citi - mastercard ****5678')
    })

    it('Next button disabled until card selected', () => {
      const wrapper = createWrapper()

      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      expect(nextButton).toBeTruthy()
      expect(nextButton!.attributes('disabled')).toBeDefined()
    })

    it('Next button enabled when card selected', async () => {
      const wrapper = createWrapper()

      const dropdown = wrapper.find('select')
      await dropdown.setValue('card-1')

      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      expect(nextButton!.attributes('disabled')).toBeUndefined()
    })

    it('Next button advances to upload step', async () => {
      const wrapper = createWrapper()

      // Select a card
      const dropdown = wrapper.find('select')
      await dropdown.setValue('card-1')

      // Click Next
      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      await nextButton!.trigger('click')

      // Should show upload step with FileDropZone
      expect(wrapper.find('.upload-step').exists()).toBe(true)
      expect(wrapper.find('[data-testid="file-drop-zone"]').exists()).toBe(true)
    })

    it('Cancel button closes modal', async () => {
      const wrapper = createWrapper()

      const cancelButton = wrapper.findAll('button').find((b) => b.text() === 'Cancel')
      expect(cancelButton).toBeTruthy()

      await cancelButton!.trigger('click')

      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(wrapper.emitted('update:visible')![0]).toEqual([false])
    })
  })

  describe('upload step', () => {
    beforeEach(() => {
      mockCards.value = [{ id: 'card-1', bank: 'Chase', brand: 'visa', last4: '1234' }]
    })

    async function navigateToUploadStep(wrapper: ReturnType<typeof createWrapper>) {
      const dropdown = wrapper.find('select')
      await dropdown.setValue('card-1')
      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      await nextButton!.trigger('click')
    }

    it('shows FileDropZone component', async () => {
      const wrapper = createWrapper()
      await navigateToUploadStep(wrapper)

      expect(wrapper.find('.upload-step').exists()).toBe(true)
      expect(wrapper.find('[data-testid="file-drop-zone"]').exists()).toBe(true)
    })

    it('FileDropZone configured correctly', async () => {
      const wrapper = createWrapper()
      await navigateToUploadStep(wrapper)

      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      expect(fileDropZone.exists()).toBe(true)
      expect(fileDropZone.props('accept')).toBe('.pdf')
      expect(fileDropZone.props('maxSize')).toBe(25 * 1024 * 1024)
    })

    it('shows validation error when emitted', async () => {
      const wrapper = createWrapper()
      await navigateToUploadStep(wrapper)

      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      await fileDropZone.vm.$emit('validation-error', 'Please select a PDF file')

      expect(wrapper.find('.p-message').exists()).toBe(true)
      expect(wrapper.text()).toContain('Please select a PDF file')
    })

    it('clears validation error when valid file selected', async () => {
      const wrapper = createWrapper()
      await navigateToUploadStep(wrapper)

      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })

      // First emit a validation error
      await fileDropZone.vm.$emit('validation-error', 'Please select a PDF file')
      expect(wrapper.find('.p-message').exists()).toBe(true)

      // Then emit a valid file selection
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      await fileDropZone.vm.$emit('update:modelValue', mockFile)

      // Error should be cleared
      expect(wrapper.find('.p-message').exists()).toBe(false)
    })

    it('Back button returns to card selection', async () => {
      const wrapper = createWrapper()
      await navigateToUploadStep(wrapper)

      // Verify we're on upload step
      expect(wrapper.find('.upload-step').exists()).toBe(true)

      // Click Back
      const backButton = wrapper.findAll('button').find((b) => b.text() === 'Back')
      await backButton!.trigger('click')

      // Should be back on card selection
      expect(wrapper.find('.card-selection').exists()).toBe(true)
    })

    it('Back button clears validation error', async () => {
      const wrapper = createWrapper()
      await navigateToUploadStep(wrapper)

      // Emit a validation error
      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      await fileDropZone.vm.$emit('validation-error', 'Please select a PDF file')
      expect(wrapper.find('.p-message').exists()).toBe(true)

      // Click Back
      const backButton = wrapper.findAll('button').find((b) => b.text() === 'Back')
      await backButton!.trigger('click')

      // Navigate back to upload step
      await navigateToUploadStep(wrapper)

      // Error should be cleared
      expect(wrapper.find('.p-message').exists()).toBe(false)
    })

    it('Upload button disabled without file', async () => {
      const wrapper = createWrapper()
      await navigateToUploadStep(wrapper)

      const uploadButton = wrapper.findAll('button').find((b) => b.text() === 'Upload')
      expect(uploadButton).toBeTruthy()
      expect(uploadButton!.attributes('disabled')).toBeDefined()
    })

    it('Upload button enabled with file selected', async () => {
      const wrapper = createWrapper()
      await navigateToUploadStep(wrapper)

      // Select a file
      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      await fileDropZone.vm.$emit('update:modelValue', mockFile)

      const uploadButton = wrapper.findAll('button').find((b) => b.text() === 'Upload')
      expect(uploadButton!.attributes('disabled')).toBeUndefined()
    })

    it('Upload button advances to processing step', async () => {
      const wrapper = createWrapper()
      await navigateToUploadStep(wrapper)

      // Select a file
      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      await fileDropZone.vm.$emit('update:modelValue', mockFile)

      // Click Upload
      const uploadButton = wrapper.findAll('button').find((b) => b.text() === 'Upload')
      await uploadButton!.trigger('click')

      // Should advance to processing step
      expect(wrapper.find('.processing-step').exists()).toBe(true)
    })

    it('selected file persists when going back and forward', async () => {
      const wrapper = createWrapper()
      await navigateToUploadStep(wrapper)

      // Select a file
      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      await fileDropZone.vm.$emit('update:modelValue', mockFile)

      // Go back to card selection
      const backButton = wrapper.findAll('button').find((b) => b.text() === 'Back')
      await backButton!.trigger('click')

      // Go forward to upload step again
      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      await nextButton!.trigger('click')

      // File should still be selected (passed as modelValue)
      const fileDropZoneAfter = wrapper.findComponent({ name: 'FileDropZone' })
      expect(fileDropZoneAfter.props('modelValue')).toEqual(mockFile)
    })
  })

  describe('processing step', () => {
    beforeEach(() => {
      mockCards.value = [{ id: 'card-1', bank: 'Chase', brand: 'visa', last4: '1234' }]
      mockUploadStatement.mockResolvedValue({ id: 'job-1', status: 'pending', statement_id: null, error_message: null, created_at: '2024-01-01', updated_at: null, completed_at: null })
    })

    async function navigateToProcessingStep(wrapper: ReturnType<typeof createWrapper>) {
      // Select a card
      const dropdown = wrapper.find('select')
      await dropdown.setValue('card-1')
      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      await nextButton!.trigger('click')

      // Select a file
      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      await fileDropZone.vm.$emit('update:modelValue', mockFile)

      // Click Upload
      const uploadButton = wrapper.findAll('button').find((b) => b.text() === 'Upload')
      await uploadButton!.trigger('click')
      await flushPromises()
    }

    it('Upload button shows loading state when uploading', async () => {
      const wrapper = createWrapper()

      // Navigate to upload step first
      const dropdown = wrapper.find('select')
      await dropdown.setValue('card-1')
      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      await nextButton!.trigger('click')

      // Select a file
      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      await fileDropZone.vm.$emit('update:modelValue', mockFile)

      // Set uploading to true
      mockIsUploading.value = true
      await wrapper.vm.$nextTick()

      // Find the Upload button (when loading, text changes to 'Loading...')
      const uploadButton = wrapper.findAll('button').find((b) => b.text() === 'Loading...')
      expect(uploadButton).toBeTruthy()
    })

    it('Upload calls uploadStatement with correct data', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      expect(mockUploadStatement).toHaveBeenCalledWith('card-1', expect.any(File))
    })

    it('Upload starts background polling', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      expect(mockStartBackgroundPolling).toHaveBeenCalled()
    })

    it('Upload transitions to processing step', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      expect(wrapper.find('.processing-step').exists()).toBe(true)
    })

    it('Processing step shows spinner', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      expect(wrapper.find('.processing-spinner').exists()).toBe(true)
    })

    it('Processing step shows "Waiting to process..." when pending', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      mockJobStatus.value = 'pending'
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Waiting to process...')
    })

    it('Processing step shows "Extracting data from PDF..." when processing', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      mockJobStatus.value = 'processing'
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Extracting data from PDF...')
    })

    it('Processing step shows close hint', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      expect(wrapper.text()).toContain('close this modal. We\'ll notify you when it\'s done.')
    })

    it('closing via dialog X during processing switches to background completion polling', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      // Simulate the composable having a jobId set (real uploadStatement does this).
      mockJobId.value = 'job-1'

      await wrapper.find('.p-dialog-header-close').trigger('click')

      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(mockStartBackgroundPolling).toHaveBeenCalledTimes(2)

      const [foregroundJobId, foregroundCb] = mockStartBackgroundPolling.mock.calls[0]
      const [backgroundJobId, backgroundCb] = mockStartBackgroundPolling.mock.calls[1]

      expect(foregroundJobId).toBe('job-1')
      expect(backgroundJobId).toBe('job-1')
      expect(typeof foregroundCb).toBe('function')
      expect(typeof backgroundCb).toBe('function')
      expect(backgroundCb).not.toBe(foregroundCb)
    })

    it('shows a toast when a background job completes while modal is closed', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      mockJobId.value = 'job-1'

      await wrapper.find('.p-dialog-header-close').trigger('click')
      await wrapper.setProps({ visible: false })

      expect(mockStartBackgroundPolling).toHaveBeenCalledTimes(2)

      const onComplete = mockStartBackgroundPolling.mock.calls[1][1] as unknown as (
        job: { status: string; statement_id: string | null; error_message: string | null }
      ) => void

      onComplete({ status: 'completed', statement_id: 'statement-123', error_message: null })

      expect(mockToastAdd).toHaveBeenCalledWith(
        expect.objectContaining({
          severity: 'success',
          summary: 'Statement Uploaded',
          group: 'upload-complete',
          data: { statementId: 'statement-123' }
        })
      )
    })

    it('shows an error toast when a background job fails while modal is closed', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      mockJobId.value = 'job-1'

      await wrapper.find('.p-dialog-header-close').trigger('click')
      await wrapper.setProps({ visible: false })

      const onComplete = mockStartBackgroundPolling.mock.calls[1][1] as unknown as (
        job: { status: string; statement_id: string | null; error_message: string | null }
      ) => void

      onComplete({ status: 'failed', statement_id: null, error_message: 'Bad PDF' })

      expect(mockToastAdd).toHaveBeenCalledWith(
        expect.objectContaining({
          severity: 'error',
          summary: 'Upload Failed',
          detail: 'Bad PDF',
          group: 'upload-complete'
        })
      )
    })

    it('Job completion (completed) transitions to success step', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      // Simulate job completing
      mockJobStatus.value = 'completed'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.success-step').exists()).toBe(true)
      expect(wrapper.find('.success-icon').exists()).toBe(true)
      expect(wrapper.text()).toContain('Statement Uploaded')
    })

    it('Job completion (partial) transitions to success step', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      // Simulate job completing with partial success
      mockJobStatus.value = 'partial'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.success-step').exists()).toBe(true)
      expect(wrapper.text()).toContain('Statement imported with partial data. Please review.')
    })

    it('View Statement emits upload-complete with statement ID and closes modal', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      mockStatementId.value = 'statement-123'
      mockJobStatus.value = 'completed'
      await wrapper.vm.$nextTick()

      const viewButton = wrapper.findAll('button').find((b) => b.text() === 'View Statement')
      expect(viewButton).toBeTruthy()

      await viewButton!.trigger('click')

      expect(wrapper.emitted('upload-complete')).toBeTruthy()
      expect(wrapper.emitted('upload-complete')![0]).toEqual(['statement-123'])
      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(wrapper.emitted('update:visible')![0]).toEqual([false])
    })

    it('Upload Another resets state and returns to card selection', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      mockStatementId.value = 'statement-123'
      mockJobStatus.value = 'completed'
      await wrapper.vm.$nextTick()

      const uploadAnotherButton = wrapper.findAll('button').find((b) => b.text() === 'Upload Another')
      expect(uploadAnotherButton).toBeTruthy()

      await uploadAnotherButton!.trigger('click')

      expect(mockResetUpload).toHaveBeenCalled()
      expect(wrapper.find('.card-selection').exists()).toBe(true)

      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      expect(nextButton).toBeTruthy()
      expect(nextButton!.attributes('disabled')).toBeDefined()
    })

    it('Job failure transitions to error step', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      // Simulate job failing
      mockJobStatus.value = 'failed'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.error-step').exists()).toBe(true)
    })

    it('Upload failure transitions to error step', async () => {
      const wrapper = createWrapper()

      // Navigate to upload step
      const dropdown = wrapper.find('select')
      await dropdown.setValue('card-1')
      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      await nextButton!.trigger('click')

      // Select a file
      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      await fileDropZone.vm.$emit('update:modelValue', mockFile)

      // Mock uploadStatement to throw an error
      mockUploadStatement.mockRejectedValue(new Error('Network error'))

      // Click Upload
      const uploadButton = wrapper.findAll('button').find((b) => b.text() === 'Upload')
      await uploadButton!.trigger('click')
      await flushPromises()

      // Should transition to error step
      expect(wrapper.find('.error-step').exists()).toBe(true)
    })

    it('network error shows friendly message', async () => {
      const wrapper = createWrapper()

      // Navigate to upload step
      const dropdown = wrapper.find('select')
      await dropdown.setValue('card-1')
      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      await nextButton!.trigger('click')

      // Select a file
      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      await fileDropZone.vm.$emit('update:modelValue', mockFile)

      // Mock uploadStatement to throw a TypeError (network error)
      mockUploadStatement.mockRejectedValue(new TypeError('Failed to fetch'))

      // Click Upload
      const uploadButton = wrapper.findAll('button').find((b) => b.text() === 'Upload')
      await uploadButton!.trigger('click')
      await flushPromises()

      // Should show friendly network error message
      expect(wrapper.find('.error-step').exists()).toBe(true)
      expect(wrapper.text()).toContain('Network error. Please check your connection and try again.')
    })

    it('modal is closable when not uploading', () => {
      const wrapper = createWrapper()
      mockIsUploading.value = false
      const dialog = wrapper.findComponent({ name: 'Dialog' })

      // canClose should be true when not uploading
      expect(dialog.props('closable')).toBe(true)
    })

    it('modal is not closable during initial upload', async () => {
      mockIsUploading.value = true
      const wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      const dialog = wrapper.findComponent({ name: 'Dialog' })

      // canClose should be false when uploading
      expect(dialog.props('closable')).toBe(false)
    })

    it('modal is closable during processing (after job is accepted)', async () => {
      const wrapper = createWrapper()

      // Navigate to processing step
      const dropdown = wrapper.find('select')
      await dropdown.setValue('card-1')
      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      await nextButton!.trigger('click')

      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      await fileDropZone.vm.$emit('update:modelValue', mockFile)

      // Click Upload to start processing
      const uploadButton = wrapper.findAll('button').find((b) => b.text() === 'Upload')
      await uploadButton!.trigger('click')
      await flushPromises()

      // After processing starts (job accepted), isUploading is false, so modal should be closable
      mockIsUploading.value = false
      await wrapper.vm.$nextTick()

      const dialog = wrapper.findComponent({ name: 'Dialog' })
      expect(dialog.props('closable')).toBe(true)
    })
  })

  describe('modal reset', () => {
    beforeEach(() => {
      mockCards.value = [{ id: 'card-1', bank: 'Chase', brand: 'visa', last4: '1234' }]
    })

    it('resets to card selection when reopened', async () => {
      const wrapper = createWrapper({ visible: true })

      // Navigate to upload step
      const dropdown = wrapper.find('select')
      await dropdown.setValue('card-1')
      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      await nextButton!.trigger('click')

      // Verify we're on upload step
      expect(wrapper.find('.upload-step').exists()).toBe(true)

      // Close and reopen modal
      await wrapper.setProps({ visible: false })
      await wrapper.setProps({ visible: true })
      await flushPromises()

      // Should be back on card selection
      expect(wrapper.find('.card-selection').exists()).toBe(true)
    })

    it('resets upload state when reopened', async () => {
      const wrapper = createWrapper({ visible: true })

      // Simulate upload state
      mockJobStatus.value = 'processing'

      // Close and reopen modal
      await wrapper.setProps({ visible: false })
      await wrapper.setProps({ visible: true })
      await flushPromises()

      expect(mockResetUpload).toHaveBeenCalled()
    })
  })

  describe('error state', () => {
    beforeEach(() => {
      mockCards.value = [{ id: 'card-1', bank: 'Chase', brand: 'visa', last4: '1234' }]
      mockUploadStatement.mockResolvedValue({ id: 'job-1', status: 'pending', statement_id: null, error_message: null, created_at: '2024-01-01', updated_at: null, completed_at: null })
    })

    async function navigateToErrorStep(wrapper: ReturnType<typeof createWrapper>) {
      // Select a card
      const dropdown = wrapper.find('select')
      await dropdown.setValue('card-1')
      const nextButton = wrapper.findAll('button').find((b) => b.text() === 'Next')
      await nextButton!.trigger('click')

      // Select a file
      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      await fileDropZone.vm.$emit('update:modelValue', mockFile)

      // Mock uploadStatement to throw an error
      mockUploadStatement.mockRejectedValue(new Error('Upload failed'))

      // Click Upload
      const uploadButton = wrapper.findAll('button').find((b) => b.text() === 'Upload')
      await uploadButton!.trigger('click')
      await flushPromises()
    }

    it('error state shows on failed status', async () => {
      const wrapper = createWrapper()

      await navigateToErrorStep(wrapper)

      expect(wrapper.find('.error-step').exists()).toBe(true)
      expect(wrapper.find('.error-icon').exists()).toBe(true)
      expect(wrapper.text()).toContain('Upload Failed')
    })

    it('error message is displayed', async () => {
      const wrapper = createWrapper()
      mockUploadErrorMessage.value = 'File too large'

      await navigateToErrorStep(wrapper)

      expect(wrapper.find('.error-text').exists()).toBe(true)
      expect(wrapper.text()).toContain('File too large')
    })

    it('duplicate error shows link', async () => {
      const wrapper = createWrapper()
      mockDuplicateJobId.value = 'duplicate-job-123'

      await navigateToErrorStep(wrapper)

      expect(wrapper.find('.duplicate-link').exists()).toBe(true)
      expect(wrapper.text()).toContain('This file was already uploaded.')

      const viewExistingButton = wrapper.findAll('button').find((b) => b.text() === 'View Existing Statement')
      expect(viewExistingButton).toBeTruthy()
    })

    it('View Existing Statement fetches job', async () => {
      const wrapper = createWrapper()
      mockDuplicateJobId.value = 'duplicate-job-123'

      await navigateToErrorStep(wrapper)

      const viewExistingButton = wrapper.findAll('button').find((b) => b.text() === 'View Existing Statement')
      await viewExistingButton!.trigger('click')

      expect(mockPollJobStatus).toHaveBeenCalledWith('duplicate-job-123')
    })

    it('View Existing Statement navigates to statement', async () => {
      const wrapper = createWrapper()
      mockDuplicateJobId.value = 'duplicate-job-123'

      await navigateToErrorStep(wrapper)

      const viewExistingButton = wrapper.findAll('button').find((b) => b.text() === 'View Existing Statement')
      await viewExistingButton!.trigger('click')
      await flushPromises()

      expect(wrapper.emitted('upload-complete')).toBeTruthy()
      expect(wrapper.emitted('upload-complete')![0]).toEqual(['statement-123'])
      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(wrapper.emitted('update:visible')![0]).toEqual([false])
    })

    it('Try Again returns to upload step', async () => {
      const wrapper = createWrapper()

      await navigateToErrorStep(wrapper)

      const tryAgainButton = wrapper.findAll('button').find((b) => b.text() === 'Try Again')
      await tryAgainButton!.trigger('click')

      expect(wrapper.find('.upload-step').exists()).toBe(true)
      expect(wrapper.find('[data-testid="file-drop-zone"]').exists()).toBe(true)
    })

    it('Try Again clears selected file', async () => {
      const wrapper = createWrapper()

      await navigateToErrorStep(wrapper)

      const tryAgainButton = wrapper.findAll('button').find((b) => b.text() === 'Try Again')
      await tryAgainButton!.trigger('click')

      const fileDropZone = wrapper.findComponent({ name: 'FileDropZone' })
      expect(fileDropZone.props('modelValue')).toBeNull()
    })

    it('error icon uses pi-times-circle', async () => {
      const wrapper = createWrapper()

      await navigateToErrorStep(wrapper)

      expect(wrapper.find('.error-icon.pi-times-circle').exists()).toBe(true)
    })

    it('non-duplicate errors do not show link', async () => {
      const wrapper = createWrapper()
      mockDuplicateJobId.value = null

      await navigateToErrorStep(wrapper)

      expect(wrapper.find('.duplicate-link').exists()).toBe(false)

      const viewExistingButton = wrapper.findAll('button').find((b) => b.text() === 'View Existing Statement')
      expect(viewExistingButton).toBeFalsy()
    })

    it('shows fallback error message when none provided', async () => {
      const wrapper = createWrapper()

      await navigateToErrorStep(wrapper)

      // After navigating, explicitly clear the error message to force fallback
      mockUploadErrorMessage.value = null
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.error-text').exists()).toBe(true)
      expect(wrapper.text()).toContain('An error occurred while uploading')
    })
  })
})
