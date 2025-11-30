import { useToast as usePrimeToast } from 'primevue/usetoast'

export const useCustomToast = () => {
  const toast = usePrimeToast()

  const showErrorToast = (message: string) => {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: message,
      life: 3000
    })
  }

  const showSuccessToast = (message: string) => {
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: message,
      life: 3000
    })
  }

  const showWarnToast = (message: string) => {
    toast.add({
      severity: 'warn',
      summary: 'Warning',
      detail: message,
      life: 3000
    })
  }

  const showInfoToast = (message: string) => {
    toast.add({
      severity: 'info',
      summary: 'Info',
      detail: message,
      life: 3000
    })
  }

  return {
    showErrorToast,
    showSuccessToast,
    showWarnToast,
    showInfoToast
  }
}

export default useCustomToast