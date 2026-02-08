"""Process upload usecase for background PDF statement processing.

This usecase handles the complete workflow of extracting data from a PDF,
converting currencies, creating statement and transaction records, and
updating the upload job status.
"""

import logging
import time
import uuid
from datetime import UTC, datetime

from sqlmodel import Session

from app.domains.card_statements.domain.models import (
    CardStatementPublic,
    StatementStatus,
)
from app.domains.credit_cards.domain.models import CreditCardPublic
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card
from app.domains.credit_cards.usecases.get_card.usecase import GetCreditCardUseCase
from app.domains.rules.domain.models import ApplyRulesRequest
from app.domains.rules.usecases.apply_rules import provide as provide_apply_rules
from app.domains.transactions.domain.models import TransactionPublic
from app.domains.upload_jobs.domain.errors import (
    CurrencyConversionError,
    ExtractionError,
    UploadJobNotFoundError,
)
from app.domains.upload_jobs.domain.models import UploadJobStatus
from app.domains.upload_jobs.repository import provide as provide_repository
from app.domains.upload_jobs.service.atomic_import import provide_atomic_import
from app.domains.upload_jobs.service.upload_job_service import UploadJobService
from app.pkgs.database import get_db_session
from app.pkgs.extraction import provide as provide_extraction
from app.pkgs.extraction.models import ExtractionResult

logger = logging.getLogger(__name__)
BALANCE_MISMATCH_REVIEW_MESSAGE = (
    "Current balance does not match the sum of transactions. "
    "Please review and edit transactions."
)


async def _import_with_atomic_service(
    session: Session,
    extraction_result: ExtractionResult,
    card_id: uuid.UUID,
    target_currency: str,
    file_path: str,
) -> tuple[CardStatementPublic, list[TransactionPublic]]:
    """Import statement using atomic import service within a transaction.

    Args:
        session: Database session
        extraction_result: Result from extraction service
        card_id: Credit card ID
        target_currency: Target currency for conversion
        file_path: Path to the stored PDF file

    Returns:
        Tuple of (created statement, list of created transactions)

    Raises:
        Exception: If import fails, transaction is rolled back
    """
    atomic_service = provide_atomic_import(session)

    if extraction_result.success and extraction_result.data:
        # Full extraction
        return await atomic_service.import_statement_atomic(
            data=extraction_result.data,
            card_id=card_id,
            target_currency=target_currency,
            source_file_path=file_path,
        )
    elif extraction_result.partial_data:
        # Partial extraction
        return await atomic_service.import_partial_statement_atomic(
            partial_data=extraction_result.partial_data,
            card_id=card_id,
            target_currency=target_currency,
            source_file_path=file_path,
        )
    else:
        raise ExtractionError(
            extraction_result.error or "Unknown extraction failure",
            model_used=extraction_result.model_used,
        )


def _apply_rules_to_statement(
    session: Session,
    user_id: uuid.UUID,
    statement_id: uuid.UUID,
) -> None:
    """Apply rules to transactions in a statement (non-blocking).

    This function applies user-defined rules to auto-tag transactions.
    Failures are logged but do not affect the overall job status.

    Args:
        session: Database session
        user_id: User ID who owns the rules
        statement_id: Statement ID containing transactions to process
    """
    try:
        apply_rules_usecase = provide_apply_rules(session)
        request = ApplyRulesRequest(statement_id=statement_id)
        result = apply_rules_usecase.execute(user_id, request)
        logger.info(
            f"Rules applied to statement {statement_id}: "
            f"{result.transactions_processed} transactions processed, "
            f"{result.tags_applied} tags applied"
        )
    except Exception as e:
        # Rules application is non-blocking - log and continue
        logger.warning(f"Failed to apply rules to statement {statement_id}: {e}")


def _get_sanitized_error_message(error: Exception) -> str:
    """Get a sanitized error message that doesn't expose internal details.

    Args:
        error: The exception that occurred

    Returns:
        A user-friendly error message
    """
    if isinstance(error, ExtractionError):
        return "Failed to extract data from PDF. The file may be corrupted or in an unsupported format."
    elif isinstance(error, CurrencyConversionError):
        return "Failed to convert currency. Please try again later."
    else:
        # For unexpected errors, return a generic message
        # The full exception details are logged server-side
        return "An unexpected error occurred while processing the statement. Please try again."


async def process_upload_job(
    job_id: uuid.UUID,
    pdf_bytes: bytes,
    card_id: uuid.UUID,
    file_path: str,
) -> None:
    """Process an uploaded PDF statement in the background.

    This function:
    1. Updates job status to PROCESSING
    2. Extracts statement data from PDF using LLM
    3. Retries with fallback model on failure
    4. Converts multi-currency balances to card's default currency
    5. Creates CardStatement and Transaction records (atomically)
    6. Applies rules to auto-tag transactions (non-blocking)
    7. Updates job to final status (COMPLETED, PARTIAL, or FAILED)

    Args:
        job_id: Upload job ID
        pdf_bytes: PDF file contents
        card_id: Credit card ID
        file_path: S3 key where PDF is stored
    """
    session = get_db_session()
    repository = provide_repository(session)
    job_service = UploadJobService(repository)
    extraction_service = provide_extraction()
    get_card_usecase: GetCreditCardUseCase = provide_get_card(session)

    try:
        # Update job to PROCESSING with retry logic
        # This handles the race condition where the background task starts
        # before the endpoint's transaction is fully committed
        logger.info(f"Starting processing for job {job_id}")
        max_retries = 5
        retry_delay = 0.5  # seconds
        for attempt in range(max_retries):
            try:
                job_service.update_status(job_id, UploadJobStatus.PROCESSING)
                break
            except UploadJobNotFoundError:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Job {job_id} not found, retrying in {retry_delay}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    # Refresh the session to get latest data
                    session.expire_all()
                else:
                    logger.warning(
                        "Aborting background processing for missing job %s "
                        "after %s retries",
                        job_id,
                        max_retries,
                    )
                    return
            except Exception:
                raise

        # Get card for default currency and user_id
        card: CreditCardPublic = get_card_usecase.execute(card_id)
        target_currency = card.default_currency
        user_id = card.user_id

        # Extract statement with primary model
        extraction_result: ExtractionResult = (
            await extraction_service.extract_statement(pdf_bytes, model_index=0)
        )

        # Retry with fallback if failed
        if not extraction_result.success and extraction_result.error:
            logger.warning(
                f"Primary extraction failed for job {job_id}: {extraction_result.error}"
            )
            job_service.increment_retry(job_id)

            extraction_result = await extraction_service.extract_statement(
                pdf_bytes, model_index=1
            )

        # Process based on extraction result
        if extraction_result.success and extraction_result.data:
            # Full extraction succeeded - use atomic import
            logger.info(f"Full extraction successful for job {job_id}")

            statement, _ = await _import_with_atomic_service(
                session=session,
                extraction_result=extraction_result,
                card_id=card_id,
                target_currency=target_currency,
                file_path=file_path,
            )
            is_pending_review = statement.status == StatementStatus.PENDING_REVIEW

            # Update job status BEFORE applying rules (rules may commit)
            if is_pending_review:
                job_service.update_status(
                    job_id,
                    UploadJobStatus.PARTIAL,
                    statement_id=statement.id,
                    error_message=BALANCE_MISMATCH_REVIEW_MESSAGE,
                    completed_at=datetime.now(UTC),
                )
                logger.info(
                    "Job %s completed with pending review due to balance mismatch",
                    job_id,
                )
            else:
                job_service.update_status(
                    job_id,
                    UploadJobStatus.COMPLETED,
                    statement_id=statement.id,
                    completed_at=datetime.now(UTC),
                )
                logger.info(f"Job {job_id} completed successfully")

            # Apply rules to new transactions (non-blocking, after job status update)
            _apply_rules_to_statement(session, user_id, statement.id)

        elif extraction_result.partial_data:
            # Partial extraction - best effort import (still atomic)
            logger.info(f"Partial extraction for job {job_id}")

            statement, _ = await _import_with_atomic_service(
                session=session,
                extraction_result=extraction_result,
                card_id=card_id,
                target_currency=target_currency,
                file_path=file_path,
            )

            # Update job status BEFORE applying rules (rules may commit)
            job_service.update_status(
                job_id,
                UploadJobStatus.PARTIAL,
                statement_id=statement.id,
                error_message=extraction_result.error,
                completed_at=datetime.now(UTC),
            )
            logger.info(f"Job {job_id} completed with partial data")

            # Apply rules to new transactions (non-blocking, after job status update)
            _apply_rules_to_statement(session, user_id, statement.id)

        else:
            # Complete failure
            error_msg = extraction_result.error or "Unknown extraction failure"
            logger.error(f"Extraction failed for job {job_id}: {error_msg}")
            raise ExtractionError(error_msg, model_used=extraction_result.model_used)

    except ExtractionError as e:
        logger.error(f"Extraction error for job {job_id}: {e}")
        try:
            job_service.update_status(
                job_id,
                UploadJobStatus.FAILED,
                error_message=_get_sanitized_error_message(e),
                completed_at=datetime.now(UTC),
            )
        except UploadJobNotFoundError:
            logger.warning(
                "Cannot mark job %s as failed after extraction error: job not found",
                job_id,
            )

    except CurrencyConversionError as e:
        logger.error(f"Currency conversion error for job {job_id}: {e}")
        try:
            job_service.update_status(
                job_id,
                UploadJobStatus.FAILED,
                error_message=_get_sanitized_error_message(e),
                completed_at=datetime.now(UTC),
            )
        except UploadJobNotFoundError:
            logger.warning(
                "Cannot mark job %s as failed after currency error: job not found",
                job_id,
            )

    except Exception as e:
        logger.exception(f"Unexpected error processing job {job_id}: {e}")
        try:
            job_service.update_status(
                job_id,
                UploadJobStatus.FAILED,
                error_message=_get_sanitized_error_message(e),
                completed_at=datetime.now(UTC),
            )
        except UploadJobNotFoundError:
            logger.warning(
                "Cannot mark job %s as failed after unexpected error: job not found",
                job_id,
            )

    finally:
        session.close()
        logger.info(f"Session closed for job {job_id}")
