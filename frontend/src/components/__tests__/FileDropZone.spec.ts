import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FileDropZone from '../FileDropZone.vue'

// Stub PrimeVue Button component
const ButtonStub = {
  name: 'Button',
  template: '<button @click="$emit(\'click\', $event)"><slot /></button>',
  props: ['icon', 'severity', 'text', 'rounded', 'aria-label']
}

describe('FileDropZone', () => {
  const defaultProps = {
    modelValue: null,
    accept: '.pdf',
    maxSize: 25 * 1024 * 1024 // 25MB
  }

  function createWrapper(props = {}) {
    return mount(FileDropZone, {
      props: { ...defaultProps, ...props },
      global: {
        stubs: {
          Button: ButtonStub
        }
      }
    })
  }

  function createFile(name: string, type: string, size?: number): File {
    const file = new File(['test content'], name, { type })
    if (size !== undefined) {
      Object.defineProperty(file, 'size', { value: size })
    }
    return file
  }

  describe('rendering', () => {
    it('renders drop zone with prompt when no file', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('.drop-zone').exists()).toBe(true)
      expect(wrapper.find('.drop-zone__prompt').exists()).toBe(true)
      expect(wrapper.find('.pi-upload').exists()).toBe(true)
      expect(wrapper.text()).toContain('Drag & drop your PDF here')
      expect(wrapper.text()).toContain('or click to browse')
    })

    it('shows file name when file selected', () => {
      const file = createFile('statement.pdf', 'application/pdf')
      const wrapper = createWrapper({ modelValue: file })

      expect(wrapper.find('.drop-zone__file').exists()).toBe(true)
      expect(wrapper.find('.drop-zone__prompt').exists()).toBe(false)
      expect(wrapper.find('.pi-file-pdf').exists()).toBe(true)
      expect(wrapper.find('.drop-zone__filename').text()).toBe('statement.pdf')
    })
  })

  describe('drag and drop', () => {
    it('drag over adds active class', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')

      await dropZone.trigger('dragover')

      expect(dropZone.classes()).toContain('drop-zone--active')
    })

    it('drag leave removes active class', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')

      // First trigger dragover to add active class
      await dropZone.trigger('dragover')
      expect(dropZone.classes()).toContain('drop-zone--active')

      // Then trigger dragleave to remove it
      await dropZone.trigger('dragleave')
      expect(dropZone.classes()).not.toContain('drop-zone--active')
    })

    it('drop with valid PDF selects file', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')
      const file = createFile('statement.pdf', 'application/pdf')

      const dataTransfer = {
        files: [file]
      }

      await dropZone.trigger('drop', { dataTransfer })

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted![0]).toEqual([file])
    })

    it('drop with non-PDF emits validation error', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')
      const file = createFile('document.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')

      const dataTransfer = {
        files: [file]
      }

      await dropZone.trigger('drop', { dataTransfer })

      const validationErrors = wrapper.emitted('validation-error')
      expect(validationErrors).toBeTruthy()
      expect(validationErrors![0]).toEqual(['Please select a PDF file'])

      // Should NOT emit update:modelValue
      expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    })

    it('drop with oversized file emits validation error', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')
      const oversizedFile = createFile('large.pdf', 'application/pdf', 30 * 1024 * 1024) // 30MB

      const dataTransfer = {
        files: [oversizedFile]
      }

      await dropZone.trigger('drop', { dataTransfer })

      const validationErrors = wrapper.emitted('validation-error')
      expect(validationErrors).toBeTruthy()
      expect(validationErrors![0]).toEqual(['File size exceeds 25MB limit'])

      // Should NOT emit update:modelValue
      expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    })
  })

  describe('file picker', () => {
    it('click opens file picker', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')
      const fileInput = wrapper.find('input[type="file"]').element as HTMLInputElement

      // Mock the click method to prevent recursive issues in test environment
      const clickSpy = vi.fn()
      fileInput.click = clickSpy

      await dropZone.trigger('click')

      expect(clickSpy).toHaveBeenCalled()
    })

    it('file selection through picker emits update', async () => {
      const wrapper = createWrapper()
      const fileInput = wrapper.find('input[type="file"]')
      const file = createFile('statement.pdf', 'application/pdf')

      // Create a mock files array
      const mockFiles = {
        0: file,
        length: 1,
        item: (index: number) => (index === 0 ? file : null)
      }

      // Simulate file selection
      Object.defineProperty(fileInput.element, 'files', {
        value: mockFiles,
        writable: false
      })

      await fileInput.trigger('change')

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted![0]).toEqual([file])
    })
  })

  describe('clear button', () => {
    it('clear button removes file', async () => {
      const file = createFile('statement.pdf', 'application/pdf')
      const wrapper = createWrapper({ modelValue: file })

      const clearButton = wrapper.find('.drop-zone__clear-btn')
      expect(clearButton.exists()).toBe(true)

      await clearButton.trigger('click')

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted![0]).toEqual([null])
    })

    it('clear button click does not propagate to open file picker', async () => {
      const file = createFile('statement.pdf', 'application/pdf')
      const wrapper = createWrapper({ modelValue: file })
      const fileInput = wrapper.find('input[type="file"]').element as HTMLInputElement

      // Spy on the click method
      const clickSpy = vi.spyOn(fileInput, 'click')

      const clearButton = wrapper.find('.drop-zone__clear-btn')
      await clearButton.trigger('click')

      // The file input click should NOT be called because stopPropagation
      expect(clickSpy).not.toHaveBeenCalled()
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')![0]).toEqual([null])
    })
  })

  describe('disabled state', () => {
    it('disabled state applies class', () => {
      const wrapper = createWrapper({ disabled: true })
      const dropZone = wrapper.find('.drop-zone')

      expect(dropZone.classes()).toContain('drop-zone--disabled')
    })

    it('disabled state prevents click interaction', async () => {
      const wrapper = createWrapper({ disabled: true })
      const dropZone = wrapper.find('.drop-zone')
      const fileInput = wrapper.find('input[type="file"]').element as HTMLInputElement

      // Mock the click method to prevent recursive issues in test environment
      const clickSpy = vi.fn()
      fileInput.click = clickSpy

      await dropZone.trigger('click')

      expect(clickSpy).not.toHaveBeenCalled()
    })

    it('disabled state prevents drop interaction', async () => {
      const wrapper = createWrapper({ disabled: true })
      const dropZone = wrapper.find('.drop-zone')
      const file = createFile('statement.pdf', 'application/pdf')

      const dataTransfer = {
        files: [file]
      }

      await dropZone.trigger('drop', { dataTransfer })

      // Should NOT emit any events
      expect(wrapper.emitted('update:modelValue')).toBeFalsy()
      expect(wrapper.emitted('validation-error')).toBeFalsy()
    })

    it('disabled state prevents drag over from adding active class', async () => {
      const wrapper = createWrapper({ disabled: true })
      const dropZone = wrapper.find('.drop-zone')

      await dropZone.trigger('dragover')

      expect(dropZone.classes()).not.toContain('drop-zone--active')
    })
  })

  describe('file extension validation', () => {
    it('accepts PDF file with uppercase extension', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')
      const file = createFile('STATEMENT.PDF', 'application/pdf')

      const dataTransfer = {
        files: [file]
      }

      await dropZone.trigger('drop', { dataTransfer })

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted![0]).toEqual([file])
    })

    it('rejects image file', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')
      const file = createFile('image.jpg', 'image/jpeg')

      const dataTransfer = {
        files: [file]
      }

      await dropZone.trigger('drop', { dataTransfer })

      const validationErrors = wrapper.emitted('validation-error')
      expect(validationErrors).toBeTruthy()
      expect(validationErrors![0]).toEqual(['Please select a PDF file'])
    })
  })

  describe('accessibility', () => {
    it('has role="button" attribute', () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')

      expect(dropZone.attributes('role')).toBe('button')
    })

    it('has tabindex="0" when enabled', () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')

      expect(dropZone.attributes('tabindex')).toBe('0')
    })

    it('has tabindex="-1" when disabled', () => {
      const wrapper = createWrapper({ disabled: true })
      const dropZone = wrapper.find('.drop-zone')

      expect(dropZone.attributes('tabindex')).toBe('-1')
    })

    it('has aria-label attribute', () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')

      const ariaLabel = dropZone.attributes('aria-label')
      expect(ariaLabel).toBeTruthy()
      expect(ariaLabel).toContain('Drop zone for PDF upload')
    })

    it('updates aria-label when file is selected', () => {
      const file = createFile('statement.pdf', 'application/pdf')
      const wrapper = createWrapper({ modelValue: file })
      const dropZone = wrapper.find('.drop-zone')

      const ariaLabel = dropZone.attributes('aria-label')
      expect(ariaLabel).toContain('Selected file:')
      expect(ariaLabel).toContain('statement.pdf')
    })

    it('has aria-disabled="false" when enabled', () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')

      expect(dropZone.attributes('aria-disabled')).toBe('false')
    })

    it('has aria-disabled="true" when disabled', () => {
      const wrapper = createWrapper({ disabled: true })
      const dropZone = wrapper.find('.drop-zone')

      expect(dropZone.attributes('aria-disabled')).toBe('true')
    })

    it('Enter key opens file picker', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')
      const fileInput = wrapper.find('input[type="file"]').element as HTMLInputElement

      const clickSpy = vi.fn()
      fileInput.click = clickSpy

      await dropZone.trigger('keydown', { key: 'Enter' })

      expect(clickSpy).toHaveBeenCalled()
    })

    it('Space key opens file picker', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')
      const fileInput = wrapper.find('input[type="file"]').element as HTMLInputElement

      const clickSpy = vi.fn()
      fileInput.click = clickSpy

      await dropZone.trigger('keydown', { key: ' ' })

      expect(clickSpy).toHaveBeenCalled()
    })

    it('Enter key is prevented default', async () => {
      const wrapper = createWrapper()
      const dropZone = wrapper.find('.drop-zone')
      const fileInput = wrapper.find('input[type="file"]').element as HTMLInputElement

      const clickSpy = vi.fn()
      fileInput.click = clickSpy

      const event = { key: 'Enter', preventDefault: vi.fn() }
      await dropZone.trigger('keydown', event)

      expect(event.preventDefault).toHaveBeenCalled()
      expect(clickSpy).toHaveBeenCalled()
    })

    it('disabled state ignores Enter key', async () => {
      const wrapper = createWrapper({ disabled: true })
      const dropZone = wrapper.find('.drop-zone')
      const fileInput = wrapper.find('input[type="file"]').element as HTMLInputElement

      const clickSpy = vi.fn()
      fileInput.click = clickSpy

      await dropZone.trigger('keydown', { key: 'Enter' })

      expect(clickSpy).not.toHaveBeenCalled()
    })

    it('disabled state ignores Space key', async () => {
      const wrapper = createWrapper({ disabled: true })
      const dropZone = wrapper.find('.drop-zone')
      const fileInput = wrapper.find('input[type="file"]').element as HTMLInputElement

      const clickSpy = vi.fn()
      fileInput.click = clickSpy

      await dropZone.trigger('keydown', { key: ' ' })

      expect(clickSpy).not.toHaveBeenCalled()
    })
  })
})
