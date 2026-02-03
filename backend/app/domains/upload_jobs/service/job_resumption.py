"""Job resumption service for handling pending/stale jobs on startup.

This module provides functionality to resume upload jobs that were
interrupted by a backend restart.
"""

import logging
from contextlib import contextmanager

from sqlmodel import Session

from app.domains.upload_jobs.domain.models import UploadJob, UploadJobStatus
from app.domains.upload_jobs.repository import provide as provide_repository
from app.domains.upload_jobs.usecases.process_upload import process_upload_job
from app.pkgs.database import get_engine
from app.pkgs.storage import provide as provide_storage

logger = logging.getLogger(__name__)


@contextmanager
def get_db_session_for_resumption():
    """Provide a database session for background tasks."""
    engine = get_engine()
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


async def resume_pending_jobs() -> None:
    """Resume pending and stale processing jobs on application startup.

    This function is called during application startup to ensure that
    any jobs that were in PENDING or PROCESSING state when the backend
    was restarted will be resumed.
    """
    logger.info("Checking for pending/stale jobs to resume...")

    with get_db_session_for_resumption() as session:
        repository = provide_repository(session)
        storage = provide_storage()

        # Get all pending jobs
        pending_jobs = repository.list_pending_jobs()
        logger.info(f"Found {len(pending_jobs)} pending jobs to resume")

        # Get stale processing jobs (stuck for more than 30 minutes)
        stale_jobs = repository.list_stale_processing_jobs(minutes=30)
        logger.info(f"Found {len(stale_jobs)} stale processing jobs to resume")

        # Combine and resume all jobs
        jobs_to_resume: list[UploadJob] = pending_jobs + stale_jobs

        for job in jobs_to_resume:
            try:
                logger.info(f"Resuming job {job.id} (status: {job.status.value})")

                # Reset stale processing jobs to pending
                if job.status == UploadJobStatus.PROCESSING:
                    repository.update_status(
                        job.id,
                        UploadJobStatus.PENDING,
                        error_message="Job was interrupted by server restart",
                    )

                # Retrieve the PDF from storage
                try:
                    pdf_bytes = storage.get_statement_pdf(job.file_path)
                except Exception as e:
                    logger.error(f"Failed to retrieve PDF for job {job.id}: {e}")
                    repository.update_status(
                        job.id,
                        UploadJobStatus.FAILED,
                        error_message="Failed to retrieve stored PDF for processing",
                    )
                    continue

                # Re-enqueue the job for processing
                # Note: We can't use BackgroundTasks here since we're at startup,
                # so we use asyncio.create_task for fire-and-forget processing
                import asyncio

                asyncio.create_task(
                    process_upload_job(
                        job_id=job.id,
                        pdf_bytes=pdf_bytes,
                        card_id=job.card_id,
                        file_path=job.file_path,
                    )
                )
                logger.info(f"Job {job.id} re-enqueued for processing")

            except Exception as e:
                logger.exception(f"Failed to resume job {job.id}: {e}")
                # Don't let one failed job stop others from resuming
                continue

    logger.info("Job resumption complete")
