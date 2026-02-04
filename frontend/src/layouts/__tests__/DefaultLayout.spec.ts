import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DefaultLayout from '../DefaultLayout.vue'

const routerPush = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: routerPush }),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    user: { full_name: 'Test User' },
    logout: vi.fn(),
  }),
}))

const ButtonStub = {
  name: 'Button',
  props: ['label', 'icon', 'type', 'size', 'text', 'outlined', 'severity', 'ariaLabel'],
  template: '<button :type="type || \'button\'" @click="$emit(\'click\', $event)">{{ label }}</button>',
}

const UploadStatementModalStub = {
  name: 'UploadStatementModal',
  props: ['visible'],
  template: '<div data-testid="upload-statement-modal" :data-visible="visible ? \'true\' : \'false\'" />',
}

const RouterLinkStub = {
  name: 'RouterLink',
  props: ['to'],
  template: '<a :href="String(to)"><slot /></a>',
}

const RouterViewStub = {
  name: 'RouterView',
  template: '<div data-testid="router-view" />',
}

describe('DefaultLayout', () => {
  it('opens upload modal on click without bubbling', async () => {
    const wrapper = mount(DefaultLayout, {
      global: {
        stubs: {
          Button: ButtonStub,
          Avatar: true,
          Menu: true,
          Toast: true,
          UploadStatementModal: UploadStatementModalStub,
          RouterLink: RouterLinkStub,
          RouterView: RouterViewStub,
        },
      },
    })

    const rootClickSpy = vi.fn()
    wrapper.element.addEventListener('click', rootClickSpy)

    const uploadButton = wrapper
      .findAll('button')
      .find((btn) => btn.text().includes('Upload Statement'))

    expect(uploadButton).toBeTruthy()

    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true })
    uploadButton!.element.dispatchEvent(clickEvent)
    await wrapper.vm.$nextTick()

    expect(clickEvent.defaultPrevented).toBe(true)
    expect(rootClickSpy).not.toHaveBeenCalled()
    expect(routerPush).not.toHaveBeenCalled()

    const modal = wrapper.get('[data-testid="upload-statement-modal"]')
    expect(modal.attributes('data-visible')).toBe('true')
  })
})

