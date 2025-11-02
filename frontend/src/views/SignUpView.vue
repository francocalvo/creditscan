<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
// Import PrimeVue components
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'

// Form state variables
const email = ref('')
const fullName = ref('')
const password = ref('')
const confirmPassword = ref('')
const formSubmitted = ref(false)

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Form validation
const isFormValid = computed(() => {
  return (
    email.value.trim() !== '' &&
    fullName.value.trim() !== '' &&
    password.value.trim() !== '' &&
    confirmPassword.value.trim() !== '' &&
    password.value === confirmPassword.value &&
    isValidEmail(email.value)
  )
})

// Email validation helper
const isValidEmail = (email: string): boolean => {
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailPattern.test(email)
}

// Password validation
const passwordErrors = computed(() => {
  if (!formSubmitted.value) return []
  
  const errors = []
  if (password.value.length < 8) {
    errors.push('Password must be at least 8 characters long')
  }
  return errors
})

const confirmPasswordError = computed(() => {
  if (!formSubmitted.value || !confirmPassword.value) return null
  
  if (password.value !== confirmPassword.value) {
    return 'Passwords do not match'
  }
  return null
})

// Form submission handler
const handleSubmit = async () => {
  formSubmitted.value = true

  if (isFormValid.value) {
    try {
      await authStore.register({
        email: email.value,
        full_name: fullName.value,
        password: password.value
      })
      
      // Auto-login after successful registration
      await authStore.login({
        username: email.value,
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
  <Card class="signup-card">
    <template #header>
      <div class="card-header">
        <h2 class="title">Sign Up</h2>
      </div>
    </template>

    <template #content>
      <form @submit.prevent="handleSubmit" class="form-container">
        <div class="form-field">
          <label for="fullName">Full Name</label>
          <div class="input-wrapper">
            <InputText
              id="fullName"
              v-model="fullName"
              placeholder="Enter your full name"
              :class="{ invalid: formSubmitted && !fullName }"
              autocomplete="name"
              class="w-full"
            />
          </div>
          <small v-if="formSubmitted && !fullName" class="error-text">Full name is required</small>
        </div>

        <div class="form-field">
          <label for="email">Email</label>
          <div class="input-wrapper">
            <InputText
              id="email"
              v-model="email"
              type="email"
              placeholder="Enter your email"
              :class="{ invalid: formSubmitted && (!email || !isValidEmail(email)) }"
              autocomplete="email"
              class="w-full"
            />
          </div>
          <small v-if="formSubmitted && !email" class="error-text">Email is required</small>
          <small v-else-if="formSubmitted && email && !isValidEmail(email)" class="error-text">
            Please enter a valid email address
          </small>
        </div>

        <div class="form-field">
          <label for="password">Password</label>
          <div class="input-wrapper">
            <Password
              id="password"
              v-model="password"
              placeholder="Enter your password"
              :toggleMask="true"
              :feedback="true"
              :class="{ invalid: formSubmitted && (!password || passwordErrors.length > 0) }"
              autocomplete="new-password"
              class="w-full"
            />
          </div>
          <small v-if="formSubmitted && !password" class="error-text">Password is required</small>
          <small
            v-for="(error, index) in passwordErrors"
            :key="index"
            class="error-text"
          >
            {{ error }}
          </small>
        </div>

        <div class="form-field">
          <label for="confirmPassword">Confirm Password</label>
          <div class="input-wrapper">
            <Password
              id="confirmPassword"
              v-model="confirmPassword"
              placeholder="Confirm your password"
              :toggleMask="true"
              :feedback="false"
              :class="{ invalid: formSubmitted && (!confirmPassword || confirmPasswordError) }"
              autocomplete="new-password"
              class="w-full"
            />
          </div>
          <small v-if="formSubmitted && !confirmPassword" class="error-text">
            Please confirm your password
          </small>
          <small v-else-if="confirmPasswordError" class="error-text">
            {{ confirmPasswordError }}
          </small>
        </div>

        <div v-if="authStore.error" class="error-message">
          <Message severity="error">{{ authStore.error.message }}</Message>
        </div>

        <div class="button-container">
          <Button 
            type="submit" 
            label="Sign Up" 
            icon="pi pi-user-plus" 
            :loading="authStore.loading"
            class="p-button-primary signup-button"
          />
        </div>

        <div class="login-link">
          <p>
            Already have an account? 
            <router-link to="/auth/login" class="link">Log In</router-link>
          </p>
        </div>
      </form>
    </template>
  </Card>
</template>

<style scoped>
/* Card styles only - layout is handled by AuthLayout */
.signup-card {
  max-width: 420px;
  width: 100%;
  margin: 0 auto;
}

/* Styles specific to the signup card and its contents */
.signup-card {
  width: 100%;
  background-color: var(--surface-card);
  border-radius: var(--border-radius);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.signup-card :deep(.p-card-body) {
  padding: 0;
}

.signup-card :deep(.p-card-content) {
  padding: 1rem 1.5rem 1.5rem;
  display: flex;
  justify-content: center;
}

.form-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.form-field {
  margin-bottom: 1.5rem;
  width: 100%;
  max-width: 320px;
  margin-left: auto;
  margin-right: auto;
}

.input-wrapper {
  width: 100%;
}

.input-wrapper :deep(.p-password),
.input-wrapper :deep(.p-inputtext) {
  width: 100%;
}

.signup-card :deep(.p-password-input) {
  width: 100%;
}

.card-header {
  padding: 1.25rem 1.5rem;
  text-align: center;
  background-color: var(--surface-section);
  border-radius: var(--border-radius) var(--border-radius) 0 0;
}

.title {
  margin: 0;
  color: var(--primary-color);
  font-weight: 600;
  font-size: 1.35rem;
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
  margin: 1.75rem auto 0;
  width: 100%;
  max-width: 320px;
  display: flex;
  justify-content: center;
}

.signup-button {
  width: 100%;
  min-height: 2.5rem;
}

.login-link {
  margin-top: 1.25rem;
  text-align: center;
  width: 100%;
  max-width: 320px;
}

.login-link p {
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

