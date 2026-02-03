"""Get upload job by ID endpoint."""

import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.upload_jobs.domain.errors import UploadJobNotFoundError
from app.domains.upload_jobs.domain.models import UploadJobPublic
from app.domains.upload_jobs.repository.upload_job_repository import (
    provide as provide_repository,
)

router = APIRouter()


@router.get("/{job_id}", response_model=UploadJobPublic)
def get_upload_job(
    session: SessionDep, current_user: CurrentUser, job_id: uuid.UUID
) -> UploadJobPublic:
    """Get upload job status by ID.

    Users can only view their own jobs.
    """
    try:
        repository = provide_repository(session)
        job = repository.get_by_id(job_id)

        # Verify user owns this job (return 404 for security)
        if job.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Upload job not found")

        # Convert to public model
        return UploadJobPublic(
            id=job.id,
            status=job.status,
            statement_id=job.statement_id,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )
    except UploadJobNotFoundError:
        raise HTTPException(status_code=404, detail="Upload job not found")
