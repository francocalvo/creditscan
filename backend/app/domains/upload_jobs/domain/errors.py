"""Upload job domain errors."""

import uuid


class UploadJobError(Exception):
    """Base exception for upload job errors."""

    pass


class UploadJobNotFoundError(UploadJobError):
    """Raised when an upload job is not found."""

    pass


class DuplicateFileError(UploadJobError):
    """Raised when a duplicate file hash is detected."""

    def __init__(self, message: str, existing_job_id: uuid.UUID):
        """Initialize DuplicateFileError.

        Args:
            message: The error message.
            existing_job_id: The ID of the existing job with the same file hash.
        """
        super().__init__(message)
        self.existing_job_id = existing_job_id
