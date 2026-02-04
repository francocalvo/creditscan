import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AddCardPlaceholder from '../AddCardPlaceholder.vue'

describe('AddCardPlaceholder', () => {
  function createWrapper() {
    return mount(AddCardPlaceholder)
  }

  describe('rendering', () => {
    it('renders the plus icon', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('.pi-plus').exists()).toBe(true)
    })

    it('renders the "Add Card" text', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('.placeholder-text').exists()).toBe(true)
      expect(wrapper.find('.placeholder-text').text()).toBe('Add Card')
    })

    it('has correct base styling', () => {
      const wrapper = createWrapper()
      const button = wrapper.find('.add-card-placeholder')

      expect(button.exists()).toBe(true)
      expect(button.attributes('type')).toBe('button')
      expect(button.attributes('aria-label')).toBe('Add new card')
    })

    it('contains placeholder-content wrapper', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('.placeholder-content').exists()).toBe(true)
    })
  })

  describe('click event', () => {
    it('emits click event when clicked', async () => {
      const wrapper = createWrapper()
      const button = wrapper.find('.add-card-placeholder')

      await button.trigger('click')

      expect(wrapper.emitted('click')).toBeTruthy()
      expect(wrapper.emitted('click')).toHaveLength(1)
    })

    it('emits click event with no payload', async () => {
      const wrapper = createWrapper()
      const button = wrapper.find('.add-card-placeholder')

      await button.trigger('click')

      const emitted = wrapper.emitted('click')
      expect(emitted![0]).toEqual([])
    })

    it('can be clicked multiple times', async () => {
      const wrapper = createWrapper()
      const button = wrapper.find('.add-card-placeholder')

      await button.trigger('click')
      await button.trigger('click')
      await button.trigger('click')

      expect(wrapper.emitted('click')).toHaveLength(3)
    })
  })

  describe('accessibility', () => {
    it('has button element as root', () => {
      const wrapper = createWrapper()
      const root = wrapper.find('button')

      expect(root.exists()).toBe(true)
    })

    it('has type="button" attribute', () => {
      const wrapper = createWrapper()
      const button = wrapper.find('button')

      expect(button.attributes('type')).toBe('button')
    })

    it('has aria-label attribute', () => {
      const wrapper = createWrapper()
      const button = wrapper.find('.add-card-placeholder')

      expect(button.attributes('aria-label')).toBe('Add new card')
    })

    it('icon has aria-hidden="true" attribute', () => {
      const wrapper = createWrapper()
      const icon = wrapper.find('.pi-plus')

      expect(icon.attributes('aria-hidden')).toBe('true')
    })

    it('is keyboard focusable', () => {
      const wrapper = createWrapper()
      const button = wrapper.find('button')

      // Buttons are focusable by default
      expect(button.element.tabIndex).toBe(0)
    })
  })

  describe('interactions', () => {
    it('responds to click events', async () => {
      const wrapper = createWrapper()

      expect(wrapper.emitted('click')).toBeFalsy()

      await wrapper.find('.add-card-placeholder').trigger('click')

      expect(wrapper.emitted('click')).toBeTruthy()
    })
  })

  describe('layout', () => {
    it('has placeholder-content wrapper', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('.placeholder-content').exists()).toBe(true)
    })
  })
})
