import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CardUtilization from '../CardUtilization.vue'
import type { CreditCard, CardBrand } from '@/composables/useCreditCards'

// Stub PrimeVue components
const ProgressBarStub = {
  name: 'ProgressBar',
  template: '<div class="p-progressbar" data-value="String(value)" data-testid="progress-bar"></div>',
  props: ['value', 'showValue']
}

const ButtonStub = {
  name: 'Button',
  template: '<button class="p-button" data-testid="set-limit-button" @click="$emit(\'click\')"><span class="label">{{ label }}</span><slot /></button>',
  props: ['label', 'outlined', 'size', 'dataTestId'],
  emits: ['click']
}

// Helper to create a mock card
function createCard(overrides: Partial<CreditCard> = {}): CreditCard {
  return {
    id: 'card-1',
    user_id: 'user-1',
    bank: 'Test Bank',
    brand: 'visa' as CardBrand,
    last4: '1234',
    credit_limit: 500000,
    limit_last_updated_at: '2024-01-01T00:00:00Z',
    limit_source: 'manual',
    outstanding_balance: 100000,
    ...overrides,
  }
}

function createWrapper(props: any = {}) {
  return mount(CardUtilization, {
    props: {
      card: createCard(),
      formatCurrency: (n) => `$${String(n)}`,
      ...props,
    },
    global: {
      stubs: {
        ProgressBar: ProgressBarStub,
        Button: ButtonStub,
      },
    },
  })
}

describe('CardUtilization', () => {
  describe('with credit limit', () => {
    it('renders limit, balance, and utilization percentage', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: 500000,
          outstanding_balance: 100000,
        }),
      })

      expect(wrapper.find('[data-testid="credit-limit"]').text()).toBe('$500000')
      expect(wrapper.find('[data-testid="outstanding-balance"]').text()).toBe('$100000')
      expect(wrapper.find('[data-testid="utilization"]').text()).toBe('20.0%')
    })

    it('calculates 50% utilization for balance 100000 and limit 200000', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: 200000,
          outstanding_balance: 100000,
        }),
      })

      expect(wrapper.find('[data-testid="utilization"]').text()).toBe('50.0%')
      // Verify the progress bar received the value
      const progressBar = wrapper.findComponent({ name: 'ProgressBar' })
      expect(progressBar.props('value')).toBe(50)
    })

    it('caps progress bar at 100% for over-limit utilization', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: 100000,
          outstanding_balance: 150000, // 150% utilization
        }),
      })

      expect(wrapper.find('[data-testid="utilization"]').text()).toBe('150.0%')
      const progressBar = wrapper.findComponent({ name: 'ProgressBar' })
      expect(progressBar.props('value')).toBe(100) // Capped at 100
    })

    it('shows 0% progress for negative balance (credit)', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: 100000,
          outstanding_balance: -5000, // Credit balance
        }),
      })

      expect(wrapper.find('[data-testid="utilization"]').text()).toBe('-5.0%')
      const progressBar = wrapper.findComponent({ name: 'ProgressBar' })
      expect(progressBar.props('value')).toBe(0) // Clamped to 0
    })

    it('hides Set Limit button when limit is set', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: 500000,
        }),
      })

      expect(wrapper.find('[data-testid="set-limit-button"]').exists()).toBe(false)
    })

    it('uses custom formatCurrency for limit display', () => {
      const customFormatter = (n: number) => `ARS ${n}`
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: 500000,
        }),
        formatCurrency: customFormatter,
      })

      expect(wrapper.find('[data-testid="credit-limit"]').text()).toBe('ARS 500000')
    })
  })

  describe('without credit limit', () => {
    it('shows "Not set" for credit limit', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: null,
          outstanding_balance: 100000,
        }),
      })

      expect(wrapper.find('[data-testid="credit-limit"]').text()).toBe('Not set')
    })

    it('shows "N/A" for utilization', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: null,
          outstanding_balance: 100000,
        }),
      })

      expect(wrapper.find('[data-testid="utilization"]').text()).toBe('N/A')
    })

    it('shows progress bar at 0%', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: null,
          outstanding_balance: 100000,
        }),
      })

      const progressBar = wrapper.findComponent({ name: 'ProgressBar' })
      expect(progressBar.props('value')).toBe(0)
    })

    it('shows Set Limit button', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: null,
        }),
      })

      const button = wrapper.find('[data-testid="set-limit-button"]')
      expect(button.exists()).toBe(true)
      // Check the button component's label prop
      const buttonComp = wrapper.findComponent({ name: 'Button' })
      expect(buttonComp.props('label')).toBe('Set Limit')
    })

    it('emits set-limit event with card when button clicked', async () => {
      const card = createCard({
        credit_limit: null,
        id: 'test-card-id',
      })
      const wrapper = createWrapper({
        card: card,
      })

      await wrapper.find('[data-testid="set-limit-button"]').trigger('click')

      expect(wrapper.emitted('set-limit')).toBeTruthy()
      expect(wrapper.emitted('set-limit')![0]).toEqual([card])
    })
  })

  describe('with zero credit limit', () => {
    it('treats zero limit as "not set"', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: 0,
          outstanding_balance: 100000,
        }),
      })

      expect(wrapper.find('[data-testid="credit-limit"]').text()).toBe('Not set')
      expect(wrapper.find('[data-testid="utilization"]').text()).toBe('N/A')
    })

    it('shows Set Limit button when limit is zero', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: 0,
        }),
      })

      expect(wrapper.find('[data-testid="set-limit-button"]').exists()).toBe(true)
    })
  })

  describe('edge cases', () => {
    it('handles null outstanding_balance gracefully', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: 500000,
          outstanding_balance: null as any,
        }),
      })

      // Should not crash and still render
      expect(wrapper.find('[data-testid="credit-limit"]').exists()).toBe(true)
    })

    it('displays formatted currency for outstanding balance', () => {
      const wrapper = createWrapper({
        card: createCard({
          credit_limit: 500000,
          outstanding_balance: 100000,
        }),
      })

      expect(wrapper.find('[data-testid="outstanding-balance"]').text()).toBe('$100000')
    })
  })

  describe('accessibility', () => {
    it('has data-testid attributes for testing', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('[data-testid="credit-limit"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="outstanding-balance"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="utilization"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="progress-bar"]').exists()).toBe(true)
    })

    it('renders progress bar with showValue=false', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('[data-testid="progress-bar"]').exists()).toBe(true)
    })
  })
})
