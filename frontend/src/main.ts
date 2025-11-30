import './assets/main.css'
import 'primeicons/primeicons.css'

import { OpenAPI } from './api'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import { VueQueryPlugin } from '@tanstack/vue-query'
import ToastService from 'primevue/toastservice'

import App from './App.vue'
import router from './router'

OpenAPI.BASE = import.meta.env.VITE_API_URL
OpenAPI.TOKEN = async () => {
  return localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || ''
}

const app = createApp(App)

app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
        prefix: 'p',
        // darkModeSelector: 'system',
        darkModeSelector: '.my-app-dark',

    }
  },
})

app.use(createPinia())
app.use(router)
app.use(VueQueryPlugin)
app.use(ToastService)

app.mount('#app')
