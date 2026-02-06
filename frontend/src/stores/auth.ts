import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { LoginService, UsersService } from '../api'
import type { UserPublic } from '../api'
import { ApiError } from '../api/core/ApiError'
import type { Body_login_login_access_token as LoginCredentials } from '../api'

// Extend the LoginCredentials type to include rememberMe
interface ExtendedLoginCredentials extends LoginCredentials {
  rememberMe?: boolean;
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(
    localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  )
  const user = ref<UserPublic | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<Error | null>(null)

  // Computed
  const isAuthenticated = computed(() => !!token.value)

  // Actions
  async function login(credentials: ExtendedLoginCredentials) {
    loading.value = true
    error.value = null

    try {
      const response = await LoginService.loginLoginAccessToken({
        formData: {
          username: credentials.username,
          password: credentials.password
        }
      })
      token.value = response.access_token
      
      // Store token based on rememberMe preference
      if (credentials.rememberMe) {
        localStorage.setItem('access_token', response.access_token)
        sessionStorage.removeItem('access_token')
      } else {
        sessionStorage.setItem('access_token', response.access_token)
        localStorage.removeItem('access_token')
      }

      // Fetch user profile after successful login
      await fetchUserProfile()

      return user.value
    } catch (err) {
      error.value = err instanceof Error ? err : new Error('Login failed')
      token.value = null
      localStorage.removeItem('access_token')
      sessionStorage.removeItem('access_token')
      throw error.value
    } finally {
      loading.value = false
    }
  }

  async function fetchUserProfile() {
    if (!token.value) return null

    loading.value = true
    try {
      user.value = await UsersService.usersGetCurrentUser()
      return user.value
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        // Token is invalid or expired
        logout()
      }
      error.value = err instanceof Error ? err : new Error('Failed to fetch user profile')
      throw error.value
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
    sessionStorage.removeItem('access_token')
  }

  async function register(userData: { email: string; password: string; full_name?: string | null }) {
    loading.value = true
    error.value = null

    try {
      const newUser = await UsersService.usersRegisterUser({ requestBody: userData })
      return newUser
    } catch (err) {
      error.value = err instanceof Error ? err : new Error('Registration failed')
      throw error.value
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(userData: Partial<UserPublic>) {
    if (!isAuthenticated.value) return null

    loading.value = true
    error.value = null

    try {
      user.value = await UsersService.usersUpdateCurrentUser({ requestBody: userData })
      return user.value
    } catch (err) {
      error.value = err instanceof Error ? err : new Error('Profile update failed')
      throw error.value
    } finally {
      loading.value = false
    }
  }

  async function changePassword(oldPassword: string, newPassword: string) {
    if (!isAuthenticated.value) return false

    loading.value = true
    error.value = null

    try {
      await UsersService.usersUpdateCurrentUserPassword({
        requestBody: {
          current_password: oldPassword,
          new_password: newPassword,
        },
      })
      return true
    } catch (err) {
      error.value = err instanceof Error ? err : new Error('Password change failed')
      throw error.value
    } finally {
      loading.value = false
    }
  }

  // Initialize - try to load user profile if token exists
  if (token.value) {
    fetchUserProfile().catch(() => {
      // Silent fail - will be handled by fetchUserProfile
    })
  }

  return {
    // State
    user,
    loading,
    error,
    token,

    // Computed
    isAuthenticated,

    // Actions
    login,
    logout,
    register,
    fetchUserProfile,
    updateProfile,
    changePassword,
  }
})
