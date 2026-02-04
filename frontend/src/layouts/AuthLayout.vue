<script setup lang="ts">
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

import logoLight from '@/assets/logo.svg'
import logoDark from '@/assets/logo-dark.svg'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isSignup = computed(() => route.name === 'signup')
const pageTitle = computed(() => (isSignup.value ? 'Sign Up' : 'Login'))

// Dark mode detection
const isDarkMode = ref(document.documentElement.classList.contains('my-app-dark'))
const logoSrc = computed(() => (isDarkMode.value ? logoDark : logoLight))

const updateDarkMode = () => {
  isDarkMode.value = document.documentElement.classList.contains('my-app-dark')
}

onMounted(() => {
  // Create a MutationObserver to watch for class changes on the document element
  const observer = new MutationObserver(updateDarkMode)
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

  // Store observer for cleanup
  ;(window as { __darkModeObserver?: MutationObserver }).__darkModeObserver = observer
})

onUnmounted(() => {
  // Clean up observer
  const observer = (window as { __darkModeObserver?: MutationObserver }).__darkModeObserver
  if (observer) {
    observer.disconnect()
    delete (window as { __darkModeObserver?: MutationObserver }).__darkModeObserver
  }
})

// Form state
const email = ref('')
const fullName = ref('')
const password = ref('')
const confirmPassword = ref('')
const formSubmitted = ref(false)

// Email validation
const isValidEmail = (email: string): boolean => {
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailPattern.test(email)
}

// Form validation
const isFormValid = computed(() => {
  const baseValid =
    email.value.trim() !== '' && password.value.trim() !== '' && isValidEmail(email.value)

  if (isSignup.value) {
    return (
      baseValid &&
      fullName.value.trim() !== '' &&
      confirmPassword.value.trim() !== '' &&
      password.value === confirmPassword.value
    )
  }
  return baseValid
})

// Password validation for signup
const passwordErrors = computed(() => {
  if (!formSubmitted.value || !isSignup.value) return []

  const errors = []
  if (password.value.length < 8) {
    errors.push('Password must be at least 8 characters long')
  }
  return errors
})

const confirmPasswordError = computed(() => {
  if (!formSubmitted.value || !isSignup.value || !confirmPassword.value) return null

  if (password.value !== confirmPassword.value) {
    return 'Passwords do not match'
  }
  return null
})

// Form submission
const handleSubmit = async () => {
  formSubmitted.value = true

  if (isFormValid.value) {
    try {
      if (isSignup.value) {
        await authStore.register({
          email: email.value,
          full_name: fullName.value,
          password: password.value,
        })

        // Auto-login after registration
        await authStore.login({
          username: email.value,
          password: password.value,
        })
      } else {
        await authStore.login({
          username: email.value,
          password: password.value,
        })
      }

      const redirectPath = (route.query.redirect as string) || '/'
      router.push(redirectPath)
    } catch {
      // Error handled by store
    }
  }
}

// Reset form when switching between login/signup
const resetExtraFields = () => {
  fullName.value = ''
  confirmPassword.value = ''
  formSubmitted.value = false
}

// Watch for route changes
import { watch } from 'vue'
watch(
  () => route.name,
  () => {
    resetExtraFields()
  },
)
</script>

<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-logo">
        <img :src="logoSrc" alt="FindDash Logo" />
      </div>

      <Card class="auth-card">
        <template #header>
          <div class="card-header">
            <transition name="fade" mode="out-in">
              <h2 :key="pageTitle" class="title">{{ pageTitle }}</h2>
            </transition>
          </div>
        </template>

        <template #content>
          <form @submit.prevent="handleSubmit" class="form-container">
            <!-- Full Name field - only for signup -->
            <transition name="slide-fade">
              <div v-if="isSignup" class="form-field" key="fullname">
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
                <small v-if="formSubmitted && !fullName" class="error-text"
                  >Full name is required</small
                >
              </div>
            </transition>

            <!-- Email field - common to both -->
            <div class="form-field" key="email">
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

            <!-- Password field - common to both -->
            <div class="form-field" key="password">
              <label for="password">Password</label>
              <div class="input-wrapper">
                <Password
                  id="password"
                  v-model="password"
                  placeholder="Enter your password"
                  :toggleMask="true"
                  :feedback="isSignup"
                  :class="{ invalid: formSubmitted && (!password || passwordErrors.length > 0) }"
                  :autocomplete="isSignup ? 'new-password' : 'current-password'"
                  class="w-full"
                />
              </div>
              <small v-if="formSubmitted && !password" class="error-text"
                >Password is required</small
              >
              <small v-for="(error, index) in passwordErrors" :key="index" class="error-text">
                {{ error }}
              </small>
            </div>

            <!-- Confirm Password field - only for signup -->
            <transition name="slide-fade">
              <div v-if="isSignup" class="form-field" key="confirm-password">
                <label for="confirmPassword">Confirm Password</label>
                <div class="input-wrapper">
                  <Password
                    id="confirmPassword"
                    v-model="confirmPassword"
                    placeholder="Confirm your password"
                    :toggleMask="true"
                    :feedback="false"
                    :class="{
                      invalid: formSubmitted && (!confirmPassword || confirmPasswordError),
                    }"
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
            </transition>

            <!-- Error message -->
            <div v-if="authStore.error" class="error-message">
              <Message severity="error">{{ authStore.error.message }}</Message>
            </div>

            <!-- Submit button -->
            <div class="button-container">
              <Button
                type="submit"
                :label="isSignup ? 'Sign Up' : 'Login'"
                :icon="isSignup ? 'pi pi-user-plus' : 'pi pi-sign-in'"
                :loading="authStore.loading"
                class="p-button-primary auth-button"
              />
            </div>

            <!-- Toggle link -->
            <div class="toggle-link">
              <p v-if="isSignup">
                Already have an account?
                <router-link to="/auth/login" class="link">Log In</router-link>
              </p>
              <p v-else>
                Don't have an account?
                <router-link to="/auth/signup" class="link">Sign Up</router-link>
              </p>
            </div>
          </form>
        </template>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.auth-layout {
  height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--surface-ground);
}

.auth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  max-width: 420px;
  width: 100%;
  padding: 1rem;
}

.auth-logo img {
  height: 100px;
  width: auto;
}

.auth-card {
  max-width: 420px;
  width: 100%;
  background-color: var(--surface-card);
  border-radius: var(--border-radius);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.auth-card :deep(.p-card-body) {
  padding: 0;
}

.auth-card :deep(.p-card-content) {
  padding: 1.5rem 1.5rem 2rem;
  display: flex;
  justify-content: center;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-header {
  padding: 1.5rem 1.5rem;
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

.auth-content {
  width: 100%;
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
  margin-bottom: 1.75rem;
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
}

.auth-button {
  width: 100%;
  min-height: 2.5rem;
}

.toggle-link {
  margin-top: 1.5rem;
  text-align: center;
  width: 100%;
  max-width: 320px;
}

.toggle-link p {
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

/* Transition for title */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Transition for extra fields */
.slide-fade-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
  max-height: 0;
  margin-bottom: 0;
  overflow: hidden;
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
  max-height: 0;
  margin-bottom: 0;
  overflow: hidden;
}

.slide-fade-enter-to,
.slide-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
  max-height: 200px;
}
</style>
