"""Upload job repository implementation."""

import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.domains.upload_jobs.domain.errors import (
    DuplicateFileError,
    UploadJobNotFoundError,
)
from app.domains.upload_jobs.domain.models import (
    UploadJob,
    UploadJobCreate,
    UploadJobStatus,
)


class UploadJobRepository:
    """Repository for upload jobs."""

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db_session = db_session

    def create(self, data: UploadJobCreate) -> UploadJob:
        """Create a new upload job."""
        # Check for duplicate file hash for the same user
        existing = self.get_by_file_hash(data.file_hash, data.user_id)
        if existing:
            raise DuplicateFileError(
                f"File with hash {data.file_hash} already exists for this user",
                existing.id,
            )

        job = UploadJob.model_validate(data)
        self.db_session.add(job)
        self.db_session.commit()
        self.db_session.refresh(job)
        return job

    def get_by_id(self, job_id: uuid.UUID) -> UploadJob:
        """Get an upload job by ID."""
        job = self.db_session.get(UploadJob, job_id)
        if not job:
            raise UploadJobNotFoundError(f"Upload job with ID {job_id} not found")
        return job

    def get_by_file_hash(self, file_hash: str, user_id: uuid.UUID) -> UploadJob | None:
        """Get an upload job by file hash and user ID."""
        query = select(UploadJob).where(
            UploadJob.file_hash == file_hash, UploadJob.user_id == user_id
        )
        result = self.db_session.exec(query)
        return result.first()

    def update_status(
        self,
        job_id: uuid.UUID,
        status: UploadJobStatus,
        **kwargs,
    ) -> UploadJob:
        """Update upload job status and optional fields.

        Args:
            job_id: The ID of the job to update.
            status: The new status.
            **kwargs: Optional fields to update (statement_id, error_message, etc.).

        Returns:
            The updated upload job.
        """
        job = self.get_by_id(job_id)
        job.status = status
        job.updated_at = datetime.utcnow()

        # Update optional fields if provided
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        self.db_session.add(job)
        self.db_session.commit()
        self.db_session.refresh(job)
        return job


def provide(session: Session) -> UploadJobRepository:
    """Provide an instance of UploadJobRepository.

    Args:
        session: The database session to use.

    Returns:
        UploadJobRepository: An instance of UploadJobRepository with the given session.
    """
    return UploadJobRepository(session)
