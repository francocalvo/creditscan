import { ref, type Ref } from 'vue'
import { OpenAPI } from '@/api'

/**
 * Represents an upload job returned by the backend.
 */
export interface UploadJob {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'partial' | 'failed'
  statement_id: string | null
  error_message: string | null
  created_at: string
  updated_at: string | null
  completed_at: string | null
}

/** Polling interval in milliseconds (5 seconds). */
const POLLING_INTERVAL_MS = 5000

/** Maximum polling attempts (10 minutes timeout). */
const MAX_POLLING_ATTEMPTS = 120

/** Regex to extract job ID from duplicate error messages. */
const DUPLICATE_JOB_ID_REGEX = /job_id: ([a-f0-9-]+)/

/**
 * Composable for handling credit card statement uploads with job polling support.
 */
export function useStatementUpload() {
  // State
  const isUploading: Ref<boolean> = ref(false)
  const jobId: Ref<string | null> = ref(null)
  const jobStatus: Ref<UploadJob['status'] | null> = ref(null)
  const statementId: Ref<string | null> = ref(null)
  const errorMessage: Ref<string | null> = ref(null)
  const duplicateJobId: Ref<string | null> = ref(null)

  // Internal polling state
  let pollingIntervalId: ReturnType<typeof setInterval> | null = null
  let pollingAttempts = 0
  let isPollingInProgress = false

  /**
   * Gets the authorization token from OpenAPI configuration.
   */
  async function getAuthToken(): Promise<string> {
    const token =
      typeof OpenAPI.TOKEN === 'function'
        ? await OpenAPI.TOKEN({} as any)
        : OpenAPI.TOKEN || ''
    return token
  }

  /**
   * Uploads a statement PDF file for a specific credit card.
   *
   * @param cardId - The ID of the credit card to upload the statement for
   * @param file - The PDF file to upload
   * @returns The upload job object from the backend
   * @throws Error if the upload fails
   */
  async function uploadStatement(cardId: string, file: File): Promise<UploadJob> {
    isUploading.value = true
    errorMessage.value = null
    duplicateJobId.value = null

    try {
      const token = await getAuthToken()

      const formData = new FormData()
      formData.append('card_id', cardId)
      formData.append('file', file)

      const response = await fetch(`${OpenAPI.BASE}/api/v1/card-statements/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          // Note: Do not set Content-Type for FormData - browser sets it with boundary
        },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const detail = errorData.detail || `Upload failed: ${response.statusText}`

        // Extract duplicate job ID from error message if present
        const duplicateMatch = detail.match(DUPLICATE_JOB_ID_REGEX)
        if (duplicateMatch) {
          duplicateJobId.value = duplicateMatch[1]
        }

        // Set error message based on status code
        if (response.status === 400) {
          errorMessage.value = detail
          throw new Error(detail)
        } else if (response.status === 403) {
          errorMessage.value = 'You can only upload to your own cards'
          throw new Error('You can only upload to your own cards')
        } else if (response.status === 404) {
          errorMessage.value = 'Credit card not found'
          throw new Error('Credit card not found')
        } else {
          errorMessage.value = detail
          throw new Error(detail)
        }
      }

      const job: UploadJob = await response.json()

      // Update state with job info
      jobId.value = job.id
      jobStatus.value = job.status
      statementId.value = job.statement_id

      return job
    } finally {
      isUploading.value = false
    }
  }

  /**
   * Polls the status of an upload job.
   *
   * @param jobIdToCheck - The ID of the job to check
   * @returns The current job status from the API
   */
  async function pollJobStatus(jobIdToCheck: string): Promise<UploadJob> {
    const token = await getAuthToken()

    const response = await fetch(`${OpenAPI.BASE}/api/v1/upload-jobs/${jobIdToCheck}`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to check job status: ${response.statusText}`)
    }

    const job: UploadJob = await response.json()

    // Update state
    jobStatus.value = job.status
    statementId.value = job.statement_id
    errorMessage.value = job.error_message ?? null

    return job
  }

  /**
   * Checks if a job status is terminal (completed, partial, or failed).
   */
  function isTerminalStatus(status: UploadJob['status']): boolean {
    return status === 'completed' || status === 'partial' || status === 'failed'
  }

  /**
   * Starts background polling for a job and invokes a callback when complete.
   *
   * @param jobIdToPoll - The ID of the job to poll
   * @param onComplete - Callback invoked when job reaches terminal status
   */
  function startBackgroundPolling(
    jobIdToPoll: string,
    onComplete: (job: UploadJob) => void
  ): void {
    // Clear any existing polling
    stopPolling()
    pollingAttempts = 0

    pollingIntervalId = setInterval(async () => {
      // Prevent overlapping async operations
      if (isPollingInProgress) {
        return
      }

      pollingAttempts++
      isPollingInProgress = true

      try {
        const job = await pollJobStatus(jobIdToPoll)

        if (isTerminalStatus(job.status)) {
          stopPolling()
          onComplete(job)
        } else if (pollingAttempts >= MAX_POLLING_ATTEMPTS) {
          // Timeout - stop polling but don't call onComplete with error
          stopPolling()
          errorMessage.value = 'Processing is taking longer than expected'
        }
      } catch (error) {
        // Silently continue polling on network errors
        console.error('Polling error:', error)

        if (pollingAttempts >= MAX_POLLING_ATTEMPTS) {
          stopPolling()
          errorMessage.value = 'Unable to check status after multiple attempts'
        }
      } finally {
        isPollingInProgress = false
      }
    }, POLLING_INTERVAL_MS)
  }

  /**
   * Stops all active polling intervals.
   */
  function stopPolling(): void {
    if (pollingIntervalId !== null) {
      clearInterval(pollingIntervalId)
      pollingIntervalId = null
    }
    pollingAttempts = 0
    isPollingInProgress = false
  }

  /**
   * Resets all state to initial values.
   */
  function reset(): void {
    stopPolling()
    isUploading.value = false
    jobId.value = null
    jobStatus.value = null
    statementId.value = null
    errorMessage.value = null
    duplicateJobId.value = null
  }

  return {
    // State
    isUploading,
    jobId,
    jobStatus,
    statementId,
    errorMessage,
    duplicateJobId,

    // Methods
    uploadStatement,
    pollJobStatus,
    startBackgroundPolling,
    stopPolling,
    reset,
  }
}
