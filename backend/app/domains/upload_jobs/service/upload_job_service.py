"""Upload job service implementation."""

import uuid
from datetime import UTC, datetime

from sqlmodel import Session

from app.domains.upload_jobs.domain.models import (
    UploadJobCreate,
    UploadJobPublic,
    UploadJobStatus,
)
from app.domains.upload_jobs.repository import provide as provide_repository
from app.domains.upload_jobs.repository.upload_job_repository import (
    UploadJobRepository,
)


class UploadJobService:
    """Service for upload jobs."""

    def __init__(self, repository: UploadJobRepository):
        """Initialize the service with a repository."""
        self.repository = repository

    def create(self, data: UploadJobCreate) -> UploadJobPublic:
        """Create a new upload job."""
        job = self.repository.create(data)
        return UploadJobPublic.model_validate(job)

    def get(self, job_id: uuid.UUID) -> UploadJobPublic:
        """Get an upload job by ID."""
        job = self.repository.get_by_id(job_id)
        return UploadJobPublic.model_validate(job)

    def update_status(
        self,
        job_id: uuid.UUID,
        status: UploadJobStatus,
        **kwargs: object,
    ) -> UploadJobPublic:
        """Update upload job status and optional fields.

        Args:
            job_id: The ID of the job to update.
            status: The new status.
            **kwargs: Optional fields to update (statement_id, error_message, etc.).

        Returns:
            The updated upload job as a public model.
        """
        job = self.repository.update_status(job_id, status, **kwargs)
        return UploadJobPublic.model_validate(job)

    def increment_retry(self, job_id: uuid.UUID) -> UploadJobPublic:
        """Increment the retry count for a job.

        Args:
            job_id: The ID of the job to update.

        Returns:
            The updated upload job as a public model.
        """
        job = self.repository.get_by_id(job_id)
        updated_job = self.repository.update_status(
            job_id,
            job.status,
            retry_count=job.retry_count + 1,
            updated_at=datetime.now(UTC),
        )
        return UploadJobPublic.model_validate(updated_job)


def provide(session: Session) -> UploadJobService:
    """Provide an instance of UploadJobService.

    Args:
        session: The database session to use.

    Returns:
        UploadJobService: An instance of UploadJobService with the given session.
    """
    return UploadJobService(provide_repository(session))
