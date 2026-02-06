import type { ApiError } from './api'
import { useCustomToast } from './composables/useToast'

export const emailPattern = {
  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
  message: 'Invalid email address',
}

export const namePattern = {
  value: /^[A-Za-z\s\u00C0-\u017F]{1,30}$/,
  message: 'Invalid name',
}

export const passwordRules = (isRequired = true) => {
  const rules: Record<string, unknown> = {
    minLength: {
      value: 8,
      message: 'Password must be at least 8 characters',
    },
  }

  if (isRequired) {
    rules.required = 'Password is required'
  }

  return rules
}

export const confirmPasswordRules = (
  getValues: () => Record<string, unknown>,
  isRequired = true,
) => {
  const rules: Record<string, unknown> = {
    validate: (value: string) => {
      const password = getValues().password || getValues().new_password
      return value === password ? true : 'The passwords do not match'
    },
  }

  if (isRequired) {
    rules.required = 'Password confirmation is required'
  }

  return rules
}

export const handleError = (err: ApiError) => {
  const { showErrorToast } = useCustomToast()
  const errDetail = (err.body as Record<string, unknown>)?.detail
  let errorMessage = typeof errDetail === 'string' ? errDetail : 'Something went wrong.'
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    const first = errDetail[0]
    if (typeof first === 'object' && first !== null && 'msg' in first) {
      const msg = (first as { msg?: unknown }).msg
      if (typeof msg === 'string' && msg.trim()) {
        errorMessage = msg
      }
    }
  }
  showErrorToast(errorMessage)
}
