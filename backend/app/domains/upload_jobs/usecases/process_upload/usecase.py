"""Process upload usecase for background PDF statement processing.

This usecase handles the complete workflow of extracting data from a PDF,
converting currencies, creating statement and transaction records, and
updating the upload job status.
"""

import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlmodel import Session

from app.domains.card_statements.domain.models import (
    CardStatementCreate,
    CardStatementPublic,
    StatementStatus,
)
from app.domains.card_statements.service import provide as provide_statement_service
from app.domains.credit_cards.domain.models import CreditCardPublic
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card
from app.domains.credit_cards.usecases.get_card.usecase import GetCreditCardUseCase
from app.domains.rules.domain.models import ApplyRulesRequest
from app.domains.rules.usecases.apply_rules import provide as provide_apply_rules
from app.domains.transactions.domain.models import (
    TransactionCreate,
    TransactionPublic,
)
from app.domains.transactions.service import provide as provide_transaction_service
from app.domains.upload_jobs.domain.errors import (
    CurrencyConversionError,
    ExtractionError,
)
from app.domains.upload_jobs.domain.models import UploadJobStatus
from app.domains.upload_jobs.service import provide as provide_upload_job_service
from app.pkgs.currency import provide as provide_currency
from app.pkgs.currency.service import CurrencyService
from app.pkgs.database import get_db_session
from app.pkgs.extraction import provide as provide_extraction
from app.pkgs.extraction.models import (
    ExtractedStatement,
    ExtractionResult,
    Money,
)

logger = logging.getLogger(__name__)


async def import_statement(
    session: Session,
    data: ExtractedStatement,
    card_id: uuid.UUID,
    target_currency: str,
    source_file_path: str,
) -> tuple[CardStatementPublic, list[TransactionPublic]]:
    """Import a successfully extracted statement.

    Args:
        session: Database session
        data: Extracted statement data
        card_id: Credit card ID
        target_currency: Target currency for conversion
        source_file_path: Path to the stored PDF file

    Returns:
        Tuple of (created statement, list of created transactions)
    """
    currency_service = provide_currency()
    statement_service = provide_statement_service(session)
    transaction_service = provide_transaction_service(session)

    # Convert balances to target currency
    previous_balance = await currency_service.convert_balance(
        data.previous_balance or [], target_currency
    )
    current_balance = await currency_service.convert_balance(
        data.current_balance, target_currency
    )
    minimum_payment = await currency_service.convert_balance(
        data.minimum_payment or [], target_currency
    )

    # Create statement
    statement_create = CardStatementCreate(
        card_id=card_id,
        period_start=data.period.start,
        period_end=data.period.end,
        close_date=data.period.end,
        due_date=data.period.due_date,
        previous_balance=previous_balance,
        current_balance=current_balance,
        minimum_payment=minimum_payment,
        currency=target_currency,
        status=StatementStatus.COMPLETE,
        source_file_path=source_file_path,
    )
    statement = statement_service.create_statement(statement_create)

    # Create transactions
    transactions = []
    for txn in data.transactions:
        transaction_create = TransactionCreate(
            statement_id=statement.id,
            txn_date=txn.date,
            payee=txn.merchant,
            description=txn.merchant,
            amount=txn.amount.amount,
            currency=txn.amount.currency,
            coupon=txn.coupon,
            installment_cur=txn.installment.current if txn.installment else None,
            installment_tot=txn.installment.total if txn.installment else None,
        )
        transaction = transaction_service.create_transaction(transaction_create)
        transactions.append(transaction)

    return statement, transactions


async def import_partial_statement(
    session: Session,
    partial_data: dict[str, object],
    card_id: uuid.UUID,
    target_currency: str,
    source_file_path: str,
) -> tuple[CardStatementPublic, list[TransactionPublic]]:
    """Import a partially extracted statement (best-effort).

    Args:
        session: Database session
        partial_data: Partially extracted data as dict
        card_id: Credit card ID
        target_currency: Target currency for conversion
        source_file_path: Path to the stored PDF file

    Returns:
        Tuple of (created statement, list of created transactions)
    """
    currency_service = provide_currency()
    statement_service = provide_statement_service(session)
    transaction_service = provide_transaction_service(session)

    # Safely extract period dates
    period = partial_data.get("period", {})
    period_start = _extract_date(period.get("start"))
    period_end = _extract_date(period.get("end"))
    due_date = _extract_date(period.get("due_date"))

    # Safely extract balances (may be Money objects or missing)
    previous_balance_amount = None
    current_balance_amount = None
    minimum_payment_amount = None

    if "previous_balance" in partial_data:
        previous_balance_amount = await _safe_convert_balance(
            partial_data.get("previous_balance"), currency_service, target_currency
        )

    if "current_balance" in partial_data:
        current_balance_amount = await _safe_convert_balance(
            partial_data.get("current_balance"), currency_service, target_currency
        )

    if "minimum_payment" in partial_data:
        minimum_payment_amount = await _safe_convert_balance(
            partial_data.get("minimum_payment"), currency_service, target_currency
        )

    # Create statement with PENDING_REVIEW status
    statement_create = CardStatementCreate(
        card_id=card_id,
        period_start=period_start,
        period_end=period_end,
        close_date=period_end,
        due_date=due_date,
        previous_balance=previous_balance_amount,
        current_balance=current_balance_amount,
        minimum_payment=minimum_payment_amount,
        currency=target_currency,
        status=StatementStatus.PENDING_REVIEW,
        source_file_path=source_file_path,
    )
    statement = statement_service.create_statement(statement_create)

    # Create transactions from partial data
    transactions = []
    raw_transactions = partial_data.get("transactions", [])
    if isinstance(raw_transactions, list):
        for i, raw_txn in enumerate(raw_transactions):
            try:
                if isinstance(raw_txn, dict):
                    txn_date = _extract_date(raw_txn.get("date"))
                    merchant = raw_txn.get("merchant")
                    amount_data = raw_txn.get("amount")

                    if txn_date and merchant and isinstance(amount_data, dict):
                        amount = Decimal(str(amount_data.get("amount", 0)))
                        currency = str(amount_data.get("currency", "ARS"))

                        transaction_create = TransactionCreate(
                            statement_id=statement.id,
                            txn_date=txn_date,
                            payee=merchant,
                            description=merchant,
                            amount=amount,
                            currency=currency,
                            coupon=raw_txn.get("coupon"),
                            installment_cur=_extract_installment(
                                raw_txn.get("installment"), "current"
                            ),
                            installment_tot=_extract_installment(
                                raw_txn.get("installment"), "total"
                            ),
                        )
                        transaction = transaction_service.create_transaction(
                            transaction_create
                        )
                        transactions.append(transaction)
                    else:
                        logger.warning(
                            f"Skipping transaction {i}: missing required fields"
                        )
            except Exception as e:
                logger.warning(f"Skipping transaction {i}: {e}")

    return statement, transactions


def _extract_date(value: object) -> date | None:
    """Safely extract date from various formats.

    Args:
        value: Date value (date string, date object, or None)

    Returns:
        Date object or None
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


async def _safe_convert_balance(
    balance_data: object,
    currency_service: CurrencyService,
    target_currency: str,
) -> Decimal | None:
    """Safely convert balance data to target currency.

    Args:
        balance_data: Balance data (list of Money, dict, or other)
        currency_service: Currency service for conversion
        target_currency: Target currency code

    Returns:
        Converted amount or None
    """
    if not balance_data:
        return None

    # Try to convert to list[Money]
    try:
        if isinstance(balance_data, list):
            # Convert dicts to Money objects
            money_list = []
            for item in balance_data:
                if isinstance(item, dict):
                    money = Money(
                        amount=Decimal(str(item.get("amount", 0))),
                        currency=str(item.get("currency", "ARS")),
                    )
                    money_list.append(money)
            if money_list:
                return await currency_service.convert_balance(
                    money_list, target_currency
                )
    except Exception as e:
        logger.warning(f"Failed to convert balance: {e}")
        return None

    return None


def _extract_installment(installment_data: object, field: str) -> int | None:
    """Safely extract installment field.

    Args:
        installment_data: Installment data (dict or None)
        field: Field name ("current" or "total")

    Returns:
        Installment value or None
    """
    if isinstance(installment_data, dict):
        value = installment_data.get(field)
        if isinstance(value, int):
            return value
    return None


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
    5. Creates CardStatement and Transaction records
    6. Applies rules to auto-tag transactions (non-blocking)
    7. Updates job to final status (COMPLETED, PARTIAL, or FAILED)

    Args:
        job_id: Upload job ID
        pdf_bytes: PDF file contents
        card_id: Credit card ID
        file_path: S3 key where PDF is stored
    """
    session = get_db_session()
    job_service = provide_upload_job_service(session)
    extraction_service = provide_extraction()
    get_card_usecase: GetCreditCardUseCase = provide_get_card(session)

    try:
        # Update job to PROCESSING
        logger.info(f"Starting processing for job {job_id}")
        job_service.update_status(job_id, UploadJobStatus.PROCESSING)

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
            # Full extraction succeeded
            logger.info(f"Full extraction successful for job {job_id}")
            statement, _ = await import_statement(
                session=session,
                data=extraction_result.data,
                card_id=card_id,
                target_currency=target_currency,
                source_file_path=file_path,
            )

            # Apply rules to new transactions (non-blocking)
            _apply_rules_to_statement(session, user_id, statement.id)

            job_service.update_status(
                job_id,
                UploadJobStatus.COMPLETED,
                statement_id=statement.id,
                completed_at=datetime.now(timezone.utc),
            )
            logger.info(f"Job {job_id} completed successfully")

        elif extraction_result.partial_data:
            # Partial extraction - best effort import
            logger.info(f"Partial extraction for job {job_id}")
            statement, _ = await import_partial_statement(
                session=session,
                partial_data=extraction_result.partial_data,
                card_id=card_id,
                target_currency=target_currency,
                source_file_path=file_path,
            )

            # Apply rules to new transactions (non-blocking)
            _apply_rules_to_statement(session, user_id, statement.id)

            job_service.update_status(
                job_id,
                UploadJobStatus.PARTIAL,
                statement_id=statement.id,
                error_message=extraction_result.error,
                completed_at=datetime.now(timezone.utc),
            )
            logger.info(f"Job {job_id} completed with partial data")

        else:
            # Complete failure
            error_msg = extraction_result.error or "Unknown extraction failure"
            logger.error(f"Extraction failed for job {job_id}: {error_msg}")
            raise ExtractionError(error_msg, model_used=extraction_result.model_used)

    except ExtractionError as e:
        logger.error(f"Extraction error for job {job_id}: {e}")
        job_service.update_status(
            job_id,
            UploadJobStatus.FAILED,
            error_message=f"Extraction failed: {str(e)}",
            completed_at=datetime.now(timezone.utc),
        )

    except CurrencyConversionError as e:
        logger.error(f"Currency conversion error for job {job_id}: {e}")
        job_service.update_status(
            job_id,
            UploadJobStatus.FAILED,
            error_message=f"Currency conversion failed: {str(e)}",
            completed_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.exception(f"Unexpected error processing job {job_id}: {e}")
        job_service.update_status(
            job_id,
            UploadJobStatus.FAILED,
            error_message=f"Processing error: {str(e)}",
            completed_at=datetime.now(timezone.utc),
        )

    finally:
        session.close()
        logger.info(f"Session closed for job {job_id}")
