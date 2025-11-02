<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
// Import PrimeVue components
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'

// Form state variables
const username = ref('')
const password = ref('')
const formSubmitted = ref(false)

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Form validation
const isFormValid = computed(() => {
  return username.value.trim() !== '' && password.value.trim() !== ''
})

// Form submission handler
const handleSubmit = async () => {
  formSubmitted.value = true

  if (isFormValid.value) {
    try {
      await authStore.login({
        username: username.value,
        password: password.value
      })
      
      // Redirect to the originally requested URL or home
      const redirectPath = route.query.redirect as string || '/'
      router.push(redirectPath)
    } catch (err) {
      // Error is handled by the store
    }
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="form-container">
            <div class="form-field">
              <label for="username">Username</label>
              <div class="input-wrapper">
                <InputText
                  id="username"
                  v-model="username"
                  placeholder="Enter your username"
                  :class="{ invalid: formSubmitted && !username }"
                  autocomplete="username"
                  class="w-full"
                />
              </div>
              <small v-if="formSubmitted && !username" class="error-text">Username required</small>
            </div>

            <div class="form-field">
              <label for="password">Password</label>
              <div class="input-wrapper">
                <Password
                  id="password"
                  v-model="password"
                  placeholder="Enter your password"
                  :toggleMask="true"
                  :feedback="false"
                  :class="{ invalid: formSubmitted && !password }"
                  autocomplete="current-password"
                  class="w-full"
                />
              </div>
              <small v-if="formSubmitted && !password" class="error-text">Password required</small>
            </div>

            <div v-if="authStore.error" class="error-message">
              <Message severity="error">{{ authStore.error.message }}</Message>
            </div>

            <div class="button-container">
              <Button 
                type="submit" 
                label="Login" 
                icon="pi pi-sign-in" 
                :loading="authStore.loading"
                class="p-button-primary login-button"
              />
            </div>

            <div class="signup-link">
              <p>
                Don't have an account? 
                <router-link to="/auth/signup" class="link">Sign Up</router-link>
              </p>
            </div>
  </form>
</template>

<style scoped>
.form-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  transition: all 0.4s ease;
}

.form-field {
  margin-bottom: 1.75rem;
  width: 100%;
  max-width: 320px;
  margin-left: auto;
  margin-right: auto;
  transition: all 0.4s ease;
}

.input-wrapper {
  width: 100%;
}

.input-wrapper :deep(.p-password),
.input-wrapper :deep(.p-inputtext) {
  width: 100%;
}

.input-wrapper :deep(.p-password-input) {
  width: 100%;
}

.form-field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  text-align: left;
}

.invalid {
  border-color: var(--red-500) !important;
}

.error-text {
  color: var(--red-500);
  display: block;
  margin-top: 0.25rem;
  text-align: left;
}

.error-message {
  margin: 1rem auto;
  width: 100%;
  max-width: 320px;
}

.button-container {
  margin: 2rem auto 0;
  width: 100%;
  max-width: 320px;
  display: flex;
  justify-content: center;
  transition: all 0.4s ease;
}

.login-button {
  width: 100%;
  min-height: 2.5rem;
}

.signup-link {
  margin-top: 1.5rem;
  text-align: center;
  width: 100%;
  max-width: 320px;
}

.signup-link p {
  margin: 0;
  color: var(--text-color-secondary);
}

.link {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.link:hover {
  color: var(--primary-color-emphasis);
  text-decoration: underline;
}
</style>
