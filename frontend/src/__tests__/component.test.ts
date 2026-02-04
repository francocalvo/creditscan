import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'

describe('Vue component test example', () => {
  it('should render component correctly', () => {
    const TestComponent = defineComponent({
      name: 'TestComponent',
      props: {
        message: {
          type: String,
          default: 'Hello World',
        },
      },
      render() {
        return h('div', { class: 'test-component' }, this.message)
      },
    })

    const wrapper = mount(TestComponent, {
      props: {
        message: 'Test Message',
      },
    })

    expect(wrapper.text()).toBe('Test Message')
    expect(wrapper.find('.test-component').exists()).toBe(true)
  })

  it('should use default prop value', () => {
    const TestComponent = defineComponent({
      name: 'TestComponent',
      props: {
        message: {
          type: String,
          default: 'Hello World',
        },
      },
      render() {
        return h('div', { class: 'test-component' }, this.message)
      },
    })

    const wrapper = mount(TestComponent)
    expect(wrapper.text()).toBe('Hello World')
  })
})
