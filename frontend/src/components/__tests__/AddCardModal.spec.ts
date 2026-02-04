import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import AddCardModal from '../AddCardModal.vue'

// Define CardBrand enum inline for the mock export
const { MockCardBrand } = vi.hoisted(() => ({
  MockCardBrand: {
    VISA: 'visa',
    MASTERCARD: 'mastercard',
    AMEX: 'amex',
    DISCOVER: 'discover',
    OTHER: 'other',
  } as const
}))

// Mock useCreditCards composable
const mockCreateCard = vi.fn()

vi.mock('@/composables/useCreditCards', () => ({
  useCreditCards: () => ({
    createCard: mockCreateCard,
    cards: [],
    isLoading: false,
    fetchCards: vi.fn(),
    getCardById: vi.fn(),
    error: ref(null)
  }),
  CardBrand: MockCardBrand,
}))

const CARD_BRANDS = MockCardBrand

const existingCards = [
  {
    id: 'card-1',
    user_id: 'user-1',
    bank: 'Chase',
    brand: CARD_BRANDS.VISA,
    last4: '1234',
  }
]

// Stub PrimeVue components
const DialogStub = {
  name: 'Dialog',
  template: `
    <div v-if="visible">
      <div class="p-dialog-mask" @click="dismissableMask && $emit('update:visible', false)"></div>
      <div class="p-dialog">
        <div class="p-dialog-header">
          <span>{{ header }}</span>
          <button v-if="closable" class="p-dialog-header-close" @click="$emit('update:visible', false)">X</button>
        </div>
        <div class="p-dialog-content">
          <slot />
        </div>
        <div class="p-dialog-footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  `,
  props: ['visible', 'modal', 'header', 'closable', 'dismissableMask', 'draggable'],
  emits: ['update:visible']
}

const InputTextStub = {
  name: 'InputText',
  template: '<input :value="modelValue" :disabled="disabled" :maxlength="maxlength" :placeholder="placeholder" :inputmode="inputmode" @input="$emit(\'update:modelValue\', $event.target.value)" />',
  props: ['modelValue', 'disabled', 'maxlength', 'placeholder', 'inputmode', 'class'],
  emits: ['update:modelValue']
}

const DropdownStub = {
  name: 'Dropdown',
  template: '<select :value="modelValue || \'\'" :disabled="disabled" @change="$emit(\'update:modelValue\', $event.target.value)"><option value="">Select a provider</option><option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option></select>',
  props: ['modelValue', 'options', 'optionLabel', 'optionValue', 'placeholder', 'disabled', 'class'],
  emits: ['update:modelValue']
}

const ButtonStub = {
  name: 'Button',
  template: '<button :disabled="disabled || loading" @click="$emit(\'click\', $event)"><i v-if="loading">Loading...</i>{{ label }}</button>',
  props: ['label', 'severity', 'outlined', 'disabled', 'loading', 'icon'],
  emits: ['click']
}

const MessageStub = {
  name: 'Message',
  template: '<div class="p-message" :class="`p-message-${severity}`"><slot /></div>',
  props: ['severity', 'closable']
}

function createWrapper(props = {}) {
  return mount(AddCardModal, {
    props: { visible: true, existingCards, ...props },
    global: {
      stubs: {
        Dialog: DialogStub,
        InputText: InputTextStub,
        Dropdown: DropdownStub,
        Button: ButtonStub,
        Message: MessageStub
      }
    }
  })
}

describe('AddCardModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockCreateCard.mockResolvedValue({
      id: 'new-card-1',
      user_id: 'user-1',
      bank: 'Wells Fargo',
      brand: CARD_BRANDS.VISA,
      last4: '4321',
    })
  })

  describe('modal visibility', () => {
    it('renders all fields when visible=true', () => {
      const wrapper = createWrapper({ visible: true })

      expect(wrapper.find('.p-dialog').exists()).toBe(true)
      expect(wrapper.find('.add-card-form').exists()).toBe(true)

      // Check all form fields are present
      expect(wrapper.find('#bank-input').exists()).toBe(true)
      expect(wrapper.find('#brand-select').exists()).toBe(true)
      expect(wrapper.find('#last4-input').exists()).toBe(true)
      expect(wrapper.find('#alias-input').exists()).toBe(true)
    })

    it('is hidden when visible=false', () => {
      const wrapper = createWrapper({ visible: false })

      expect(wrapper.find('.p-dialog').exists()).toBe(false)
    })

    it('emits update:visible when X clicked', async () => {
      const wrapper = createWrapper({ visible: true })

      await wrapper.find('.p-dialog-header-close').trigger('click')

      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(wrapper.emitted('update:visible')![0]).toEqual([false])
    })

    it('emits update:visible when backdrop clicked', async () => {
      const wrapper = createWrapper({ visible: true })

      await wrapper.find('.p-dialog-mask').trigger('click')

      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(wrapper.emitted('update:visible')![0]).toEqual([false])
    })
  })

  describe('form fields', () => {
    it('provider dropdown contains all 5 options', () => {
      const wrapper = createWrapper()

      const select = wrapper.find('#brand-select')
      const options = select.findAll('option')

      // Should have 5 options + 1 placeholder
      expect(options.length).toBe(6)

      // Check option values
      const optionValues = options.slice(1).map(opt => opt.attributes('value'))
      expect(optionValues).toContain('visa')
      expect(optionValues).toContain('mastercard')
      expect(optionValues).toContain('amex')
      expect(optionValues).toContain('discover')
      expect(optionValues).toContain('other')
    })

    it('last4 input has maxlength=4 and numeric inputmode', () => {
      const wrapper = createWrapper()

      const last4Input = wrapper.find('#last4-input')

      expect(last4Input.attributes('maxlength')).toBe('4')
      expect(last4Input.attributes('inputmode')).toBe('numeric')
    })

    it('alias field has placeholder hint', () => {
      const wrapper = createWrapper()

      const hints = wrapper.findAll('.field-hint')
      const aliasHint = hints.find(h => h.text().includes('friendly name'))
      expect(aliasHint).toBeTruthy()
    })
  })

  describe('validation', () => {
    it('shows no validation errors initially', () => {
      const wrapper = createWrapper()

      const errorMessages = wrapper.findAll('.p-error')
      expect(errorMessages.length).toBe(0)
    })

    it('shows bank error on submit with empty bank', async () => {
      const wrapper = createWrapper()

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Bank name is required')
    })

    it('shows provider error on submit with no provider', async () => {
      const wrapper = createWrapper()

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Please select a provider')
    })

    it('shows last4 error on submit with empty last4', async () => {
      const wrapper = createWrapper()

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Last 4 digits are required')
    })

    it('shows last4 error with "Must be exactly 4 digits" for invalid format', async () => {
      const wrapper = createWrapper()

      // Enter invalid last4 (not 4 digits)
      const last4Input = wrapper.find('#last4-input')
      await last4Input.setValue('12a')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Must be exactly 4 digits')
    })

    it('shows last4 error with "Must be exactly 4 digits" for 3 digits', async () => {
      const wrapper = createWrapper()

      const last4Input = wrapper.find('#last4-input')
      await last4Input.setValue('123')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Must be exactly 4 digits')
    })

    it('does not show duplicate error for unique card', async () => {
      const wrapper = createWrapper()

      // Enter unique card details
      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.text()).not.toContain('A card with this bank, provider, and last 4 digits already exists')
    })

    it('shows duplicate error for exact match (case-sensitive bank)', async () => {
      const wrapper = createWrapper()

      // Enter duplicate card details
      await wrapper.find('#bank-input').setValue('Chase')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('1234')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('A card with this bank, provider, and last 4 digits already exists')
    })

    it('shows duplicate error with case-insensitive bank matching', async () => {
      const wrapper = createWrapper()

      // Enter duplicate card with different bank casing
      await wrapper.find('#bank-input').setValue('CHASE') // uppercase
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('1234')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('A card with this bank, provider, and last 4 digits already exists')
    })

    it('shows duplicate error with whitespace-normalized bank matching', async () => {
      const wrapper = createWrapper()

      // Enter duplicate card with extra whitespace
      await wrapper.find('#bank-input').setValue('  Chase  ')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('1234')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('A card with this bank, provider, and last 4 digits already exists')
    })

    it('blocks API call when validation fails', async () => {
      const wrapper = createWrapper()

      // Submit empty form
      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(mockCreateCard).not.toHaveBeenCalled()
    })
  })

  describe('submission', () => {
    it('calls createCard with correct data', async () => {
      const wrapper = createWrapper()

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')
      await wrapper.find('#alias-input').setValue('My WF Card')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(mockCreateCard).toHaveBeenCalledWith({
        bank: 'Wells Fargo',
        brand: CARD_BRANDS.VISA,
        last4: '4321',
        alias: 'My WF Card',
      })
    })

    it('trims whitespace from bank name', async () => {
      const wrapper = createWrapper()

      await wrapper.find('#bank-input').setValue('  Wells Fargo  ')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(mockCreateCard).toHaveBeenCalledWith(
        expect.objectContaining({
          bank: 'Wells Fargo', // trimmed
        })
      )
    })

    it('sends undefined for empty alias', async () => {
      const wrapper = createWrapper()

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')
      // Leave alias empty

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(mockCreateCard).toHaveBeenCalledWith(
        expect.objectContaining({
          alias: undefined,
        })
      )
    })

    it('trims whitespace from alias', async () => {
      const wrapper = createWrapper()

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')
      await wrapper.find('#alias-input').setValue('  My WF Card  ')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(mockCreateCard).toHaveBeenCalledWith(
        expect.objectContaining({
          alias: 'My WF Card', // trimmed
        })
      )
    })

    it('disables form inputs during submission', async () => {
      const wrapper = createWrapper()

      // Keep createCard pending
      mockCreateCard.mockImplementation(() => new Promise(() => {}))

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await wrapper.vm.$nextTick()

      // All inputs should be disabled
      expect(wrapper.find('#bank-input').attributes('disabled')).toBeDefined()
      expect(wrapper.find('#brand-select').attributes('disabled')).toBeDefined()
      expect(wrapper.find('#last4-input').attributes('disabled')).toBeDefined()
      expect(wrapper.find('#alias-input').attributes('disabled')).toBeDefined()
    })

    it('disables action buttons during submission', async () => {
      const wrapper = createWrapper()

      // Keep createCard pending
      mockCreateCard.mockImplementation(() => new Promise(() => {}))

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await wrapper.vm.$nextTick()

      // Both buttons should be disabled
      const buttons = wrapper.findAll('button')
      buttons.forEach(btn => {
        expect(btn.attributes('disabled')).toBeDefined()
      })
    })

    it('shows loading state on Save button', async () => {
      const wrapper = createWrapper()

      // Keep createCard pending
      mockCreateCard.mockImplementation(() => new Promise(() => {}))

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await wrapper.vm.$nextTick()

      // Save button should show loading state
      const saveButton = wrapper.findAll('button').find((b) => b.text().includes('Save'))
      expect(saveButton!.find('i').text()).toContain('Loading...')
    })

    it('disables modal close during submission', async () => {
      const wrapper = createWrapper()

      // Keep createCard pending
      mockCreateCard.mockImplementation(() => new Promise(() => {}))

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await wrapper.vm.$nextTick()

      // Dialog should not be closable
      expect(wrapper.find('.p-dialog-header-close').exists()).toBe(false)
    })
  })

  describe('successful submission', () => {
    it('emits card-created with returned card', async () => {
      const wrapper = createWrapper()

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.emitted('card-created')).toBeTruthy()
      expect(wrapper.emitted('card-created')![0]).toEqual([
        {
          id: 'new-card-1',
          user_id: 'user-1',
          bank: 'Wells Fargo',
          brand: CARD_BRANDS.VISA,
          last4: '4321',
        }
      ])
    })

    it('emits update:visible(false) after successful creation', async () => {
      const wrapper = createWrapper()

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(wrapper.emitted('update:visible')![0]).toEqual([false])
    })

    it('resets form fields after successful creation', async () => {
      const wrapper = createWrapper()

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')
      await wrapper.find('#alias-input').setValue('My Card')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      // Reopen modal by setting props (simulating parent)
      await wrapper.setProps({ visible: false })
      await wrapper.setProps({ visible: true })

      // Fields should be empty
      expect((wrapper.find('#bank-input').element as HTMLInputElement).value).toBe('')
      expect((wrapper.find('#last4-input').element as HTMLInputElement).value).toBe('')
      expect((wrapper.find('#alias-input').element as HTMLInputElement).value).toBe('')
      expect((wrapper.find('#brand-select').element as HTMLSelectElement).value).toBe('')
    })
  })

  describe('server errors', () => {
    it('shows inline Message on server error', async () => {
      const wrapper = createWrapper()

      // Mock createCard to reject
      mockCreateCard.mockRejectedValue(new Error('Bank not found'))

      await wrapper.find('#bank-input').setValue('Unknown Bank')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      // Should show error message
      expect(wrapper.find('.server-error').exists()).toBe(true)
      expect(wrapper.text()).toContain('Bank not found')
    })

    it('keeps modal open on server error', async () => {
      const wrapper = createWrapper()

      // Mock createCard to reject
      mockCreateCard.mockRejectedValue(new Error('Server error'))

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      // Modal should still be visible
      expect(wrapper.find('.p-dialog').exists()).toBe(true)

      // update:visible should NOT be emitted
      expect(wrapper.emitted('update:visible')).toBeFalsy()
    })

    it('re-enables form after server error', async () => {
      const wrapper = createWrapper()

      // Mock createCard to reject
      mockCreateCard.mockRejectedValue(new Error('Server error'))

      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')

      await wrapper.findAll('button').find((b) => b.text() === 'Save')!.trigger('click')
      await flushPromises()

      // Form should be re-enabled
      expect(wrapper.find('#bank-input').attributes('disabled')).toBeUndefined()
      expect(wrapper.find('#brand-select').attributes('disabled')).toBeUndefined()
      expect(wrapper.find('#last4-input').attributes('disabled')).toBeUndefined()
      expect(wrapper.find('#alias-input').attributes('disabled')).toBeUndefined()
    })
  })

  describe('cancel', () => {
    it('emits update:visible(false) when Cancel clicked', async () => {
      const wrapper = createWrapper()

      const cancelButton = wrapper.findAll('button').find((b) => b.text() === 'Cancel')
      await cancelButton!.trigger('click')

      expect(wrapper.emitted('update:visible')).toBeTruthy()
      expect(wrapper.emitted('update:visible')![0]).toEqual([false])
    })

    it('resets form fields when Cancel clicked', async () => {
      const wrapper = createWrapper()

      // Fill in form
      await wrapper.find('#bank-input').setValue('Wells Fargo')
      await wrapper.find('#brand-select').setValue(CARD_BRANDS.VISA)
      await wrapper.find('#last4-input').setValue('4321')
      await wrapper.find('#alias-input').setValue('My Card')

      const cancelButton = wrapper.findAll('button').find((b) => b.text() === 'Cancel')
      await cancelButton!.trigger('click')

      // Reopen modal
      await wrapper.setProps({ visible: true })

      // Fields should be empty
      expect((wrapper.find('#bank-input').element as HTMLInputElement).value).toBe('')
      expect((wrapper.find('#last4-input').element as HTMLInputElement).value).toBe('')
      expect((wrapper.find('#alias-input').element as HTMLInputElement).value).toBe('')
      expect((wrapper.find('#brand-select').element as HTMLSelectElement).value).toBe('')
    })
  })
})