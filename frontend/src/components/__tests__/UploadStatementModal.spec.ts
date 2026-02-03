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
const mockJobStatus = ref<string | null>(null)
const mockStatementId = ref<string | null>(null)
const mockUploadErrorMessage = ref<string | null>(null)
const mockUploadStatement = vi.fn()
const mockStartBackgroundPolling = vi.fn()
const mockResetUpload = vi.fn()

vi.mock('@/composables/useStatementUpload', () => ({
  useStatementUpload: () => ({
    isUploading: mockIsUploading,
    jobStatus: mockJobStatus,
    errorMessage: mockUploadErrorMessage,
    statementId: mockStatementId,
    uploadStatement: mockUploadStatement,
    startBackgroundPolling: mockStartBackgroundPolling,
    reset: mockResetUpload,
  })
}))

// Stub PrimeVue components
const DialogStub = {
  name: 'Dialog',
  template: `
    <div v-if="visible" class="p-dialog">
      <div class="p-dialog-header">
        <span>{{ header }}</span>
        <button class="p-dialog-header-close" @click="$emit('update:visible', false)">X</button>
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
  props: ['label', 'severity', 'outlined', 'disabled', 'loading', 'icon', 'iconPos'],
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
    mockJobStatus.value = null
    mockStatementId.value = null
    mockUploadErrorMessage.value = null
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

      expect(wrapper.text()).toContain('close this window and we\'ll continue processing')
    })

    it('Job completion (completed) transitions to success step', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      // Simulate job completing
      mockJobStatus.value = 'completed'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.success-step').exists()).toBe(true)
    })

    it('Job completion (partial) transitions to success step', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      // Simulate job completing with partial success
      mockJobStatus.value = 'partial'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.success-step').exists()).toBe(true)
    })

    it('Job failure transitions to error step', async () => {
      const wrapper = createWrapper()

      await navigateToProcessingStep(wrapper)

      // Simulate job failing
      mockJobStatus.value = 'failed'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.error-step').exists()).toBe(true)
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
})
