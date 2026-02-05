import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import {
  type Body_login_login_access_token as AccessToken,
  type ApiError,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from '@/api'
import { OpenAPI } from '@/api/core/OpenAPI'
// import { handleError } from '@/utils/error-handler'

// Check if user is logged in based on token presence
export const isLoggedIn = (): boolean => {
  return localStorage.getItem('access_token') !== null
}

// Set up the authorization header when token is available
export const setupApiAuth = (): void => {
  const token = localStorage.getItem('access_token')
  if (token) {
    OpenAPI.TOKEN = token
  } else {
    OpenAPI.TOKEN = undefined
  }
}

export default function useAuth() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const error = ref<string | null>(null)

  // Initialize auth on composable creation
  setupApiAuth()

  // Current user query
  const {
    data: user,
    isLoading,
    refetch: refreshUser,
  } = useQuery<UserPublic | null, Error>({
    queryKey: ['currentUser'],
    queryFn: () => UsersService.usersGetCurrentUser(),
    enabled: isLoggedIn(),
    staleTime: 5 * 60 * 1000, // Consider user data fresh for 5 minutes
    retry: false, // Don't retry on auth errors
  })

  // Sign up mutation
  const signUp = useMutation({
    mutationFn: (data: UserRegister) => UsersService.usersRegisterUser({ requestBody: data }),
    onSuccess: () => {
      router.push('/login')
    },
    onError: (err: ApiError) => {
      // handleError(err, error)
      // FIXME: this to use the error handler
      if (err.status === 400) {
        error.value = 'Invalid data provided'
      } else if (err.status === 409) {
        error.value = 'User already exists'
      } else {
        error.value = 'An unexpected error occurred'
      }
    },
  })

  // Login function
  const login = async (data: AccessToken) => {
    const response = await LoginService.loginLoginAccessToken({
      formData: data,
    })
    localStorage.setItem('access_token', response.access_token)
    setupApiAuth() // Update API auth header
  }

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      refreshUser() // Fetch user after login
      router.push('/')
    },
    onError: (err: ApiError) => {
      // handleError(err, error)
      // FIXME: handle error properly
      // Fix this to use the error handler
      if (err.status === 401) {
        error.value = 'Invalid credentials'
      } else {
        error.value = 'An unexpected error occurred'
      }
    },
  })

  // Logout function
  const logout = () => {
    localStorage.removeItem('access_token')
    setupApiAuth() // Update API auth header
    queryClient.clear() // Clear query cache on logout
    router.push('/login')
  }

  // Update password mutation
  const updatePassword = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      UsersService.usersUpdateCurrentUserPassword({ requestBody: data }),
    onSuccess: () => {
      error.value = null
    },
    onError: (err: ApiError) => {
      // handleError(err, error)
      // FIXME: handle error properly
      // Fix this to use the error handler
      if (err.status === 400) {
        error.value = 'Invalid password provided'
      } else if (err.status === 401) {
        error.value = 'Current password is incorrect'
      } else {
        error.value = 'An unexpected error occurred'
      }
    },
  })

  // Update user profile mutation
  const updateProfile = useMutation({
    mutationFn: (data: any) => UsersService.usersUpdateCurrentUser({ requestBody: data }), // eslint-disable-line @typescript-eslint/no-explicit-any
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['currentUser'] })
    },
    onError: (err: ApiError) => {
      // handleError(err, error)
      // FIXME: handle error properly
      // Fix this to use the error handler
      if (err.status === 400) {
        error.value = 'Invalid data provided'
      } else if (err.status === 401) {
        error.value = 'Unauthorized'
      } else {
        error.value = 'An unexpected error occurred'
      }
    },
  })

  // Delete account mutation
  const deleteAccount = useMutation({
    mutationFn: () => UsersService.usersDeleteCurrentUser(),
    onSuccess: () => {
      localStorage.removeItem('access_token')
      setupApiAuth()
      queryClient.clear()
      router.push('/login')
    },
    onError: (err: ApiError) => {
      // handleError(err, error)
      // FIXME: handle error properly
      // Fix this to use the error handler
      if (err.status === 400) {
        error.value = 'Invalid request'
      } else if (err.status === 401) {
        error.value = 'Unauthorized'
      } else {
        error.value = 'An unexpected error occurred'
      }
    },
  })

  return {
    // State
    user,
    isLoggedIn: computed(() => isLoggedIn()),
    isLoading,
    error,

    // Auth actions
    signUp: signUp.mutate,
    login: loginMutation.mutate,
    logout,
    updatePassword: updatePassword.mutate,
    updateProfile: updateProfile.mutate,
    deleteAccount: deleteAccount.mutate,

    // Loading states
    isSigningUp: computed(() => signUp.isPending.value),
    isLoggingIn: computed(() => loginMutation.isPending.value),
    isUpdatingPassword: computed(() => updatePassword.isPending.value),
    isUpdatingProfile: computed(() => updateProfile.isPending.value),
    isDeletingAccount: computed(() => deleteAccount.isPending.value),

    // Helpers
    resetError: () => (error.value = null),
    refreshUser,
  }
}
