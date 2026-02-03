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


class ExtractionError(UploadJobError):
    """Raised when PDF extraction fails."""

    def __init__(self, message: str, model_used: str | None = None):
        """Initialize ExtractionError.

        Args:
            message: The error message.
            model_used: The model that was used when extraction failed.
        """
        super().__init__(message)
        self.model_used = model_used


class CurrencyConversionError(UploadJobError):
    """Raised when currency conversion fails."""

    def __init__(self, message: str, source_currency: str | None = None):
        """Initialize CurrencyConversionError.

        Args:
            message: The error message.
            source_currency: The currency that failed to convert.
        """
        super().__init__(message)
        self.source_currency = source_currency


class StorageError(UploadJobError):
    """Raised when S3/Garage storage operations fail."""

    def __init__(self, message: str, operation: str | None = None):
        """Initialize StorageError.

        Args:
            message: The error message.
            operation: The storage operation that failed (upload, download, delete).
        """
        super().__init__(message)
        self.operation = operation


class RulesApplicationError(UploadJobError):
    """Raised when rules application fails (non-fatal)."""

    def __init__(self, message: str, statement_id: uuid.UUID | None = None):
        """Initialize RulesApplicationError.

        Args:
            message: The error message.
            statement_id: The statement ID for which rules failed.
        """
        super().__init__(message)
        self.statement_id = statement_id
