"""Upload statement endpoint for PDF file uploads."""

import hashlib
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.api.deps import CurrentUser, SessionDep
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card
from app.domains.upload_jobs.domain.errors import DuplicateFileError
from app.domains.upload_jobs.domain.models import UploadJobCreate, UploadJobPublic
from app.domains.upload_jobs.service import provide as provide_upload_job_service
from app.domains.upload_jobs.usecases.process_upload import process_upload_job
from app.pkgs.storage import provide as provide_storage

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes

router = APIRouter()


@router.post("/upload", response_model=UploadJobPublic, status_code=202)
def upload_statement(
    session: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    card_id: Annotated[uuid.UUID, Form()],
    file: Annotated[UploadFile, File()],
) -> UploadJobPublic:
    """Upload a PDF statement for processing.

    Validates the PDF file, stores it in S3, creates an upload job,
    and schedules background processing.

    Args:
        session: Database session
        current_user: Authenticated user
        background_tasks: FastAPI BackgroundTasks for async processing
        card_id: ID of the credit card for this statement
        file: PDF file to upload

    Returns:
        Upload job with status "pending"

    Raises:
        HTTPException 400: File is not a PDF, exceeds size limit, or is a duplicate
        HTTPException 403: User doesn't own the credit card
        HTTPException 404: Credit card not found
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a name")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Read and validate file size (using file.file.read() which is synchronous)
    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 25MB limit")

    # Verify card ownership
    try:
        get_card_usecase = provide_get_card(session)
        card = get_card_usecase.execute(card_id)

        if not current_user.is_superuser and card.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only upload statements for your own cards",
            )
    except CreditCardNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Credit card not found",
        )

    # Calculate SHA-256 hash
    file_hash = hashlib.sha256(contents).hexdigest()

    # Store PDF in S3
    storage = provide_storage()
    file_path = storage.store_statement_pdf(current_user.id, file_hash, contents)

    # Create upload job
    job_service = provide_upload_job_service(session)
    try:
        job_create = UploadJobCreate(
            user_id=current_user.id,
            card_id=card_id,
            file_hash=file_hash,
            file_path=file_path,
            file_size=len(contents),
        )
        job = job_service.create(job_create)
    except DuplicateFileError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Duplicate file already uploaded (job_id: {e.existing_job_id})",
        )

    # Schedule background task
    background_tasks.add_task(
        process_upload_job,
        job_id=job.id,
        pdf_bytes=contents,
        card_id=card_id,
        file_path=file_path,
    )

    return job
