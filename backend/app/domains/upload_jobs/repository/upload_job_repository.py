"""Upload job repository implementation."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
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
        job = UploadJob.model_validate(data)

        # Use a nested transaction (savepoint) if the session is already in a transaction
        # This ensures that a rollback only affects this operation, not the entire transaction
        if self.db_session.in_transaction():
            nested = self.db_session.begin_nested()
        else:
            nested = None

        self.db_session.add(job)
        try:
            if nested:
                nested.commit()
            else:
                self.db_session.commit()
            self.db_session.refresh(job)
        except IntegrityError as e:
            if nested:
                nested.rollback()
            else:
                self.db_session.rollback()
            # Check if it's the unique constraint violation on (user_id, file_hash)
            error_str = str(e).lower()
            if (
                "uq_upload_job_user_file_hash" in error_str
                or "unique constraint failed" in error_str
                or "unique constraint" in error_str
            ):
                # Find the existing job
                existing = self.get_by_file_hash(data.file_hash, data.user_id)
                if existing:
                    raise DuplicateFileError(
                        f"File with hash {data.file_hash} already exists for this user",
                        existing.id,
                    )
            # Re-raise if not a duplicate file error or no existing job found
            raise
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
        **kwargs: object,
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
        job.updated_at = datetime.now(timezone.utc)

        # Update optional fields if provided
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        self.db_session.add(job)
        self.db_session.commit()
        self.db_session.refresh(job)
        return job

    def list_pending_jobs(self) -> list[UploadJob]:
        """List all jobs with pending status.

        Returns:
            List of pending upload jobs that need to be resumed.
        """
        query = select(UploadJob).where(UploadJob.status == UploadJobStatus.PENDING)
        result = self.db_session.exec(query)
        return list(result)

    def list_stale_processing_jobs(self, minutes: int = 30) -> list[UploadJob]:
        """List jobs stuck in processing state for too long.

        Args:
            minutes: Number of minutes to consider a job stale.

        Returns:
            List of stale processing jobs that may need to be resumed.
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        query = select(UploadJob).where(
            UploadJob.status == UploadJobStatus.PROCESSING,
            UploadJob.updated_at < cutoff,
        )
        result = self.db_session.exec(query)
        return list(result)


def provide(session: Session) -> UploadJobRepository:
    """Provide an instance of UploadJobRepository.

    Args:
        session: The database session to use.

    Returns:
        UploadJobRepository: An instance of UploadJobRepository with the given session.
    """
    return UploadJobRepository(session)
