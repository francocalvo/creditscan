import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { useStatementUpload } from '../useStatementUpload'
import { OpenAPI } from '@/api'
import type { UploadJob } from '../useStatementUpload'

// Mock OpenAPI module
vi.mock('@/api', () => ({
  OpenAPI: {
    BASE: 'https://api.example.com',
    TOKEN: 'test-token',
  },
}))

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('useStatementUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset fetch mock for each test
    mockFetch.mockReset()
  })

  afterEach(() => {
    // Clean up any active polling
    vi.useRealTimers()
  })

  describe('uploadStatement', () => {
    it('sends correct FormData with card_id and file fields', async () => {
      const mockFile = new File(['test content'], 'statement.pdf', { type: 'application/pdf' })
      const mockJob: UploadJob = {
        id: 'job-123',
        status: 'pending',
        statement_id: null,
        error_message: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
        completed_at: null,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 202,
        json: async () => mockJob,
      })

      const { uploadStatement, isUploading, jobId, jobStatus, statementId } = useStatementUpload()

      const result = await uploadStatement('card-456', mockFile)

      expect(mockFetch).toHaveBeenCalledTimes(1)
      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/api/v1/card-statements/upload',
        expect.objectContaining({
          method: 'POST',
          headers: {
            Authorization: 'Bearer test-token',
          },
          body: expect.any(FormData),
        })
      )

      // Verify FormData has correct fields
      const callArgs = mockFetch.mock.calls[0]
      const formData = callArgs[1].body as FormData
      expect(formData.get('card_id')).toBe('card-456')
      expect(formData.get('file')).toBe(mockFile)
      expect(isUploading.value).toBe(false)
      expect(jobId.value).toBe('job-123')
      expect(jobStatus.value).toBe('pending')
      expect(statementId.value).toBeNull()
      expect(result).toEqual(mockJob)
    })

    it('returns job on 202 response', async () => {
      const mockFile = new File(['test'], 'statement.pdf', { type: 'application/pdf' })
      const mockJob: UploadJob = {
        id: 'job-789',
        status: 'pending',
        statement_id: null,
        error_message: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
        completed_at: null,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 202,
        json: async () => mockJob,
      })

      const { uploadStatement, jobId, jobStatus, statementId } = useStatementUpload()

      const result = await uploadStatement('card-123', mockFile)

      expect(result).toEqual(mockJob)
      expect(jobId.value).toBe('job-789')
      expect(jobStatus.value).toBe('pending')
      expect(statementId.value).toBeNull()
    })

    it('handles 400 error', async () => {
      const mockFile = new File(['test'], 'statement.pdf', { type: 'application/pdf' })
      const errorDetail = 'Invalid file format'

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: errorDetail }),
      })

      const { uploadStatement, errorMessage } = useStatementUpload()

      await expect(uploadStatement('card-123', mockFile)).rejects.toThrow(errorDetail)
      expect(errorMessage.value).toBe(errorDetail)
    })

    it('handles 403 error', async () => {
      const mockFile = new File(['test'], 'statement.pdf', { type: 'application/pdf' })

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Forbidden' }),
      })

      const { uploadStatement, errorMessage } = useStatementUpload()

      await expect(uploadStatement('card-123', mockFile)).rejects.toThrow(
        'You can only upload to your own cards'
      )
      expect(errorMessage.value).toBe('You can only upload to your own cards')
    })

    it('handles 404 error', async () => {
      const mockFile = new File(['test'], 'statement.pdf', { type: 'application/pdf' })

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      })

      const { uploadStatement, errorMessage } = useStatementUpload()

      await expect(uploadStatement('card-123', mockFile)).rejects.toThrow('Credit card not found')
      expect(errorMessage.value).toBe('Credit card not found')
    })

    it('extracts duplicate job ID from error message', async () => {
      const mockFile = new File(['test'], 'statement.pdf', { type: 'application/pdf' })
      const errorMessage = 'Duplicate file detected. job_id: abc-123-def-456'

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: errorMessage }),
      })

      const { uploadStatement, duplicateJobId } = useStatementUpload()

      await expect(uploadStatement('card-123', mockFile)).rejects.toThrow()
      expect(duplicateJobId.value).toBe('abc-123-def-456')
    })
  })

  describe('pollJobStatus', () => {
    it('returns job status correctly', async () => {
      const mockJob: UploadJob = {
        id: 'job-123',
        status: 'processing',
        statement_id: null,
        error_message: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:01:00Z',
        completed_at: null,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockJob,
      })

      const { pollJobStatus, jobStatus, statementId, errorMessage } = useStatementUpload()

      const result = await pollJobStatus('job-123')

      expect(result).toEqual(mockJob)
      expect(jobStatus.value).toBe('processing')
      expect(statementId.value).toBeNull()
      expect(errorMessage.value).toBeNull()
    })

    it('sets error_message from job when present', async () => {
      const mockJob: UploadJob = {
        id: 'job-123',
        status: 'failed',
        statement_id: null,
        error_message: 'Processing failed',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:01:00Z',
        completed_at: '2024-01-01T00:01:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockJob,
      })

      const { pollJobStatus, errorMessage } = useStatementUpload()

      await pollJobStatus('job-123')

      expect(errorMessage.value).toBe('Processing failed')
    })

    it('clears error_message when job has no error', async () => {
      const mockJob: UploadJob = {
        id: 'job-123',
        status: 'completed',
        statement_id: 'stmt-456',
        error_message: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:01:00Z',
        completed_at: '2024-01-01T00:01:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockJob,
      })

      const { pollJobStatus, errorMessage } = useStatementUpload()

      // Set an error first
      errorMessage.value = 'Previous error'
      await pollJobStatus('job-123')

      expect(errorMessage.value).toBeNull()
    })
  })

  describe('startBackgroundPolling', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    it('calls callback on terminal status (completed)', async () => {
      const mockJob: UploadJob = {
        id: 'job-123',
        status: 'completed',
        statement_id: 'stmt-456',
        error_message: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:01:00Z',
        completed_at: '2024-01-01T00:01:00Z',
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockJob,
      })

      const onComplete = vi.fn()
      const { startBackgroundPolling, stopPolling } = useStatementUpload()

      startBackgroundPolling('job-123', onComplete)

      // Advance timers to trigger polling
      await vi.advanceTimersByTimeAsync(5000)

      expect(onComplete).toHaveBeenCalledTimes(1)
      expect(onComplete).toHaveBeenCalledWith(mockJob)
      stopPolling()
    })

    it('calls callback on terminal status (partial)', async () => {
      const mockJob: UploadJob = {
        id: 'job-123',
        status: 'partial',
        statement_id: 'stmt-456',
        error_message: 'Some transactions failed',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:01:00Z',
        completed_at: '2024-01-01T00:01:00Z',
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockJob,
      })

      const onComplete = vi.fn()
      const { startBackgroundPolling, stopPolling } = useStatementUpload()

      startBackgroundPolling('job-123', onComplete)

      await vi.advanceTimersByTimeAsync(5000)

      expect(onComplete).toHaveBeenCalledTimes(1)
      expect(onComplete).toHaveBeenCalledWith(mockJob)
      stopPolling()
    })

    it('calls callback on terminal status (failed)', async () => {
      const mockJob: UploadJob = {
        id: 'job-123',
        status: 'failed',
        statement_id: null,
        error_message: 'Processing failed',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:01:00Z',
        completed_at: '2024-01-01T00:01:00Z',
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockJob,
      })

      const onComplete = vi.fn()
      const { startBackgroundPolling, stopPolling } = useStatementUpload()

      startBackgroundPolling('job-123', onComplete)

      await vi.advanceTimersByTimeAsync(5000)

      expect(onComplete).toHaveBeenCalledTimes(1)
      expect(onComplete).toHaveBeenCalledWith(mockJob)
      stopPolling()
    })

    it('continues polling for non-terminal status', async () => {
      const pendingJob: UploadJob = {
        id: 'job-123',
        status: 'pending',
        statement_id: null,
        error_message: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
        completed_at: null,
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => pendingJob,
      })

      const onComplete = vi.fn()
      const { startBackgroundPolling, stopPolling } = useStatementUpload()

      startBackgroundPolling('job-123', onComplete)

      // Poll multiple times
      await vi.advanceTimersByTimeAsync(15000)

      expect(onComplete).not.toHaveBeenCalled()
      stopPolling()
    })

    it('clears polling interval when callback is invoked', async () => {
      const mockJob: UploadJob = {
        id: 'job-123',
        status: 'completed',
        statement_id: 'stmt-456',
        error_message: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:01:00Z',
        completed_at: '2024-01-01T00:01:00Z',
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockJob,
      })

      const onComplete = vi.fn()
      const { startBackgroundPolling, jobStatus } = useStatementUpload()

      startBackgroundPolling('job-123', onComplete)

      await vi.advanceTimersByTimeAsync(5000)

      expect(jobStatus.value).toBe('completed')
      // The interval should be cleared, so advancing further shouldn't trigger more calls
      mockFetch.mockClear()
      await vi.advanceTimersByTimeAsync(5000)

      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  describe('stopPolling', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    it('clears active polling intervals', async () => {
      const mockJob: UploadJob = {
        id: 'job-123',
        status: 'pending',
        statement_id: null,
        error_message: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
        completed_at: null,
      }

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockJob,
      })

      const onComplete = vi.fn()
      const { startBackgroundPolling, stopPolling } = useStatementUpload()

      startBackgroundPolling('job-123', onComplete)

      // Poll once
      await vi.advanceTimersByTimeAsync(5000)

      // Stop polling
      stopPolling()

      mockFetch.mockClear()

      // Advance timers - should not trigger more polling
      await vi.advanceTimersByTimeAsync(5000)

      expect(mockFetch).not.toHaveBeenCalled()
      expect(onComplete).not.toHaveBeenCalled()
    })
  })

  describe('reset', () => {
    it('clears all state to initial values', async () => {
      const mockFile = new File(['test'], 'statement.pdf', { type: 'application/pdf' })
      const mockJob: UploadJob = {
        id: 'job-123',
        status: 'pending',
        statement_id: null,
        error_message: 'Test error',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
        completed_at: null,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 202,
        json: async () => mockJob,
      })

      const { uploadStatement, reset, isUploading, jobId, jobStatus, statementId, errorMessage, duplicateJobId } =
        useStatementUpload()

      // Set some state
      await uploadStatement('card-123', mockFile)
      duplicateJobId.value = 'dup-456'

      // Reset
      reset()

      expect(isUploading.value).toBe(false)
      expect(jobId.value).toBeNull()
      expect(jobStatus.value).toBeNull()
      expect(statementId.value).toBeNull()
      expect(errorMessage.value).toBeNull()
      expect(duplicateJobId.value).toBeNull()
    })
  })
})
