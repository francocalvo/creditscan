"""Unit tests for process_upload usecase."""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest

from app.domains.card_statements.domain.models import (
    CardStatementPublic,
    StatementStatus,
)
from app.domains.credit_cards.domain.models import CreditCardPublic
from app.domains.rules.domain.models import ApplyRulesResponse
from app.domains.transactions.domain.models import (
    TransactionPublic,
)
from app.domains.upload_jobs.domain.errors import (
    CurrencyConversionError,
    ExtractionError,
)
from app.domains.upload_jobs.domain.models import UploadJobStatus
from app.domains.upload_jobs.usecases.process_upload.usecase import (
    _apply_rules_to_statement,
    _get_sanitized_error_message,
    _import_with_atomic_service,
    process_upload_job,
)
from app.pkgs.extraction.models import (
    ExtractedCycle,
    ExtractedStatement,
    ExtractedTransaction,
    Money,
)


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock(spec=Mock)
    session.close = Mock()
    return session


@pytest.fixture
def mock_job_service():
    """Mock upload job service."""
    service = Mock()
    service.update_status = Mock()
    service.increment_retry = Mock()
    return service


@pytest.fixture
def mock_extraction_service():
    """Mock extraction service."""
    service = Mock()
    service.extract_statement = AsyncMock()
    return service


@pytest.fixture
def mock_currency_service():
    """Mock currency service."""
    service = Mock()
    service.convert_balance = AsyncMock(return_value=Decimal("100.00"))
    return service


@pytest.fixture
def mock_statement_service():
    """Mock statement service."""
    service = Mock()
    service.create_statement = Mock(return_value=_mock_statement())
    return service


@pytest.fixture
def mock_transaction_service():
    """Mock transaction service."""
    service = Mock()
    service.create_transaction = Mock(return_value=_mock_transaction())
    return service


@pytest.fixture
def mock_card():
    """Mock credit card."""
    return CreditCardPublic(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        bank="Test Bank",
        brand="visa",
        last4="1234",
        default_currency="ARS",
    )


def _mock_statement(statement_id=None):
    """Create a mock statement."""
    return CardStatementPublic(
        id=statement_id or uuid.uuid4(),
        card_id=uuid.uuid4(),
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
        close_date=date(2024, 1, 31),
        due_date=date(2024, 2, 10),
        previous_balance=Decimal("0.00"),
        current_balance=Decimal("100.00"),
        minimum_payment=Decimal("10.00"),
        is_fully_paid=False,
        currency="ARS",
        status=StatementStatus.COMPLETE,
        source_file_path="statements/test.pdf",
    )


def _mock_transaction(transaction_id=None):
    """Create a mock transaction."""
    return TransactionPublic(
        id=transaction_id or uuid.uuid4(),
        statement_id=uuid.uuid4(),
        txn_date=date(2024, 1, 15),
        payee="Test Merchant",
        description="Test purchase",
        amount=Decimal("50.00"),
        currency="ARS",
    )


def _mock_extracted_statement():
    """Create a mock extracted statement."""
    return ExtractedStatement(
        statement_id="stmt-123",
        period=ExtractedCycle(
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            due_date=date(2024, 2, 10),
        ),
        previous_balance=[Money(amount=Decimal("0.00"), currency="ARS")],
        current_balance=[Money(amount=Decimal("100.00"), currency="ARS")],
        minimum_payment=[Money(amount=Decimal("10.00"), currency="ARS")],
        transactions=[
            ExtractedTransaction(
                date=date(2024, 1, 15),
                merchant="Test Merchant",
                amount=Money(amount=Decimal("50.00"), currency="ARS"),
            )
        ],
    )


class TestSanitizedErrorMessages:
    """Test suite for error message sanitization."""

    def test_extraction_error_sanitized(self):
        """Given: ExtractionError
        When: _get_sanitized_error_message() called
        Then: returns user-friendly message without internals
        """
        error = ExtractionError(
            "LLM API failed with status 500", model_used="test-model"
        )
        result = _get_sanitized_error_message(error)

        assert "corrupted" in result.lower() or "unsupported" in result.lower()
        assert "500" not in result
        assert "LLM" not in result
        assert "test-model" not in result

    def test_currency_conversion_error_sanitized(self):
        """Given: CurrencyConversionError
        When: _get_sanitized_error_message() called
        Then: returns user-friendly message without internals
        """
        error = CurrencyConversionError("API key invalid", source_currency="USD")
        result = _get_sanitized_error_message(error)

        assert "currency" in result.lower()
        assert "API key" not in result
        assert "invalid" not in result.lower()

    def test_generic_error_sanitized(self):
        """Given: generic Exception
        When: _get_sanitized_error_message() called
        Then: returns generic message without exception details
        """
        error = Exception("Database connection failed: psycopg2.OperationalError")
        result = _get_sanitized_error_message(error)

        assert "unexpected" in result.lower()
        assert "psycopg2" not in result
        assert "OperationalError" not in result
        assert "Database connection failed" not in result


class TestAtomicImport:
    """Test suite for atomic import functionality."""

    @pytest.mark.asyncio
    async def test_import_statement_atomic_success(
        self, mock_session, mock_currency_service
    ):
        """Given: valid extracted data
        When: _import_with_atomic_service() called
        Then: returns statement and transactions
        """
        with patch(
            "app.domains.upload_jobs.usecases.process_upload.usecase.provide_atomic_import"
        ) as mock_provide:
            mock_atomic_service = Mock()
            mock_atomic_service.import_statement_atomic = AsyncMock(
                return_value=(_mock_statement(), [_mock_transaction()])
            )
            mock_provide.return_value = mock_atomic_service

            extraction_result = Mock()
            extraction_result.success = True
            extraction_result.data = _mock_extracted_statement()
            extraction_result.partial_data = None

            result = await _import_with_atomic_service(
                session=mock_session,
                extraction_result=extraction_result,
                card_id=uuid.uuid4(),
                target_currency="ARS",
                file_path="statements/test.pdf",
            )

            assert result[0] is not None
            assert len(result[1]) == 1
            mock_atomic_service.import_statement_atomic.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_partial_statement_atomic(
        self, mock_session, mock_currency_service
    ):
        """Given: partial extraction data
        When: _import_with_atomic_service() called
        Then: returns statement with partial data
        """
        with patch(
            "app.domains.upload_jobs.usecases.process_upload.usecase.provide_atomic_import"
        ) as mock_provide:
            mock_atomic_service = Mock()
            mock_atomic_service.import_partial_statement_atomic = AsyncMock(
                return_value=(_mock_statement(), [_mock_transaction()])
            )
            mock_provide.return_value = mock_atomic_service

            extraction_result = Mock()
            extraction_result.success = False
            extraction_result.data = None
            extraction_result.partial_data = {"period": {"start": "2024-01-01"}}
            extraction_result.error = "Validation failed"
            extraction_result.model_used = "test-model"

            result = await _import_with_atomic_service(
                session=mock_session,
                extraction_result=extraction_result,
                card_id=uuid.uuid4(),
                target_currency="ARS",
                file_path="statements/test.pdf",
            )

            assert result[0] is not None
            mock_atomic_service.import_partial_statement_atomic.assert_called_once()


class TestProcessUploadJob:
    """Test suite for process_upload_job function."""

    @pytest.mark.asyncio
    async def test_updates_job_to_processing_at_start(
        self,
        mock_session,
        mock_job_service,
        mock_extraction_service,
        mock_card,
    ):
        """Given: pending job
        When: process_upload_job() starts
        Then: job_service.update_status(job_id, PROCESSING) called
        """
        job_id = uuid.uuid4()
        card_id = uuid.uuid4()

        with (
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.get_db_session",
                return_value=mock_session,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_repository",
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.UploadJobService",
                return_value=mock_job_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_extraction",
                return_value=mock_extraction_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_get_card",
            ) as mock_provide_get_card,
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase._import_with_atomic_service",
                new_callable=AsyncMock,
            ) as mock_import,
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase._apply_rules_to_statement",
            ),
        ):
            mock_get_card = Mock()
            mock_get_card.execute = Mock(return_value=mock_card)
            mock_provide_get_card.return_value = mock_get_card

            mock_extraction_service.extract_statement.return_value = Mock(
                success=True,
                data=_mock_extracted_statement(),
                partial_data=None,
                error=None,
                model_used="test-model",
            )

            mock_import.return_value = (_mock_statement(), [_mock_transaction()])

            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"test pdf",
                card_id=card_id,
                file_path="statements/test.pdf",
            )

            mock_job_service.update_status.assert_any_call(
                job_id, UploadJobStatus.PROCESSING
            )

    @pytest.mark.asyncio
    async def test_creates_statement_on_success(
        self,
        mock_session,
        mock_job_service,
        mock_extraction_service,
        mock_card,
    ):
        """Given: successful extraction
        When: process_upload_job() completes
        Then: atomic import service is called
        """
        job_id = uuid.uuid4()
        card_id = uuid.uuid4()

        with (
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.get_db_session",
                return_value=mock_session,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_repository",
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.UploadJobService",
                return_value=mock_job_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_extraction",
                return_value=mock_extraction_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_get_card",
            ) as mock_provide_get_card,
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase._import_with_atomic_service",
                new_callable=AsyncMock,
            ) as mock_import,
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase._apply_rules_to_statement",
            ),
        ):
            mock_get_card = Mock()
            mock_get_card.execute = Mock(return_value=mock_card)
            mock_provide_get_card.return_value = mock_get_card

            mock_extraction_service.extract_statement.return_value = Mock(
                success=True,
                data=_mock_extracted_statement(),
                partial_data=None,
                error=None,
                model_used="test-model",
            )

            mock_statement = _mock_statement()
            mock_import.return_value = (mock_statement, [_mock_transaction()])

            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"test pdf",
                card_id=card_id,
                file_path="statements/test.pdf",
            )

            mock_import.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_completed_with_statement_id(
        self,
        mock_session,
        mock_job_service,
        mock_extraction_service,
        mock_card,
    ):
        """Given: successful processing
        When: process_upload_job() completes
        Then: job_service.update_status(job_id, COMPLETED, statement_id=...) called
        """
        job_id = uuid.uuid4()
        card_id = uuid.uuid4()
        statement_id = uuid.uuid4()

        with (
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.get_db_session",
                return_value=mock_session,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_repository",
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.UploadJobService",
                return_value=mock_job_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_extraction",
                return_value=mock_extraction_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_get_card",
            ) as mock_provide_get_card,
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase._import_with_atomic_service",
                new_callable=AsyncMock,
            ) as mock_import,
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase._apply_rules_to_statement",
            ),
        ):
            mock_get_card = Mock()
            mock_get_card.execute = Mock(return_value=mock_card)
            mock_provide_get_card.return_value = mock_get_card

            mock_extraction_service.extract_statement.return_value = Mock(
                success=True,
                data=_mock_extracted_statement(),
                partial_data=None,
                error=None,
                model_used="test-model",
            )

            mock_statement = _mock_statement(statement_id=statement_id)
            mock_import.return_value = (mock_statement, [_mock_transaction()])

            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"test pdf",
                card_id=card_id,
                file_path="statements/test.pdf",
            )

            mock_job_service.update_status.assert_any_call(
                job_id,
                UploadJobStatus.COMPLETED,
                statement_id=statement_id,
                completed_at=ANY,
            )

    @pytest.mark.asyncio
    async def test_retry_on_extraction_failure(
        self,
        mock_session,
        mock_job_service,
        mock_extraction_service,
        mock_card,
    ):
        """Given: first extraction fails
        When: retry is attempted
        Then: fallback model is used
        """
        job_id = uuid.uuid4()
        card_id = uuid.uuid4()

        with (
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.get_db_session",
                return_value=mock_session,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_repository",
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.UploadJobService",
                return_value=mock_job_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_extraction",
                return_value=mock_extraction_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_get_card",
            ) as mock_provide_get_card,
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase._import_with_atomic_service",
                new_callable=AsyncMock,
            ) as mock_import,
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase._apply_rules_to_statement",
            ),
        ):
            mock_get_card = Mock()
            mock_get_card.execute = Mock(return_value=mock_card)
            mock_provide_get_card.return_value = mock_get_card

            # First call fails, second succeeds
            mock_extraction_service.extract_statement.side_effect = [
                Mock(
                    success=False,
                    data=None,
                    partial_data=None,
                    error="Primary model failed",
                    model_used="primary",
                ),
                Mock(
                    success=True,
                    data=_mock_extracted_statement(),
                    partial_data=None,
                    error=None,
                    model_used="fallback",
                ),
            ]

            mock_import.return_value = (_mock_statement(), [_mock_transaction()])

            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"test pdf",
                card_id=card_id,
                file_path="statements/test.pdf",
            )

            assert mock_extraction_service.extract_statement.call_count == 2
            mock_job_service.increment_retry.assert_called_once_with(job_id)

    @pytest.mark.asyncio
    async def test_partial_import_on_validation_failure(
        self,
        mock_session,
        mock_job_service,
        mock_extraction_service,
        mock_card,
    ):
        """Given: extraction returns partial data
        When: processing handles it
        Then: statement is created with available data and status=PENDING_REVIEW
        """
        job_id = uuid.uuid4()
        card_id = uuid.uuid4()

        with (
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.get_db_session",
                return_value=mock_session,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_repository",
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.UploadJobService",
                return_value=mock_job_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_extraction",
                return_value=mock_extraction_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_get_card",
            ) as mock_provide_get_card,
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase._import_with_atomic_service",
                new_callable=AsyncMock,
            ) as mock_import,
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase._apply_rules_to_statement",
            ),
        ):
            mock_get_card = Mock()
            mock_get_card.execute = Mock(return_value=mock_card)
            mock_provide_get_card.return_value = mock_get_card

            mock_extraction_service.extract_statement.return_value = Mock(
                success=False,
                data=None,
                partial_data={"period": {"start": "2024-01-01"}},
                error="Validation failed",
                model_used="test-model",
            )

            mock_statement = _mock_statement()
            mock_import.return_value = (mock_statement, [_mock_transaction()])

            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"test pdf",
                card_id=card_id,
                file_path="statements/test.pdf",
            )

            mock_job_service.update_status.assert_any_call(
                job_id,
                UploadJobStatus.PARTIAL,
                statement_id=mock_statement.id,
                error_message="Validation failed",
                completed_at=ANY,
            )

    @pytest.mark.asyncio
    async def test_job_failed_with_sanitized_error_message(
        self,
        mock_session,
        mock_job_service,
        mock_extraction_service,
        mock_card,
    ):
        """Given: unrecoverable error
        When: processing fails
        Then: status=FAILED and error_message is sanitized
        """
        job_id = uuid.uuid4()
        card_id = uuid.uuid4()

        with (
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.get_db_session",
                return_value=mock_session,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_repository",
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.UploadJobService",
                return_value=mock_job_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_extraction",
                return_value=mock_extraction_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_get_card",
            ) as mock_provide_get_card,
        ):
            mock_get_card = Mock()
            mock_get_card.execute = Mock(return_value=mock_card)
            mock_provide_get_card.return_value = mock_get_card

            mock_extraction_service.extract_statement.return_value = Mock(
                success=False,
                data=None,
                partial_data=None,
                error="LLM API crashed with stack trace: ...",
                model_used="test-model",
            )

            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"test pdf",
                card_id=card_id,
                file_path="statements/test.pdf",
            )

            mock_job_service.update_status.assert_any_call(
                job_id,
                UploadJobStatus.FAILED,
                error_message=ANY,
                completed_at=ANY,
            )
            # Verify the error message is sanitized (not the raw error)
            call_args = mock_job_service.update_status.call_args_list[-1]
            error_msg = call_args.kwargs.get("error_message", "")
            assert "LLM" not in error_msg
            assert "stack trace" not in error_msg

    @pytest.mark.asyncio
    async def test_session_cleanup_on_error(
        self,
        mock_session,
        mock_job_service,
        mock_extraction_service,
        mock_card,
    ):
        """Given: exception during processing
        When: finally block runs
        Then: session is closed
        """
        job_id = uuid.uuid4()
        card_id = uuid.uuid4()

        with (
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.get_db_session",
                return_value=mock_session,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_repository",
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.UploadJobService",
                return_value=mock_job_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_extraction",
                return_value=mock_extraction_service,
            ),
            patch(
                "app.domains.upload_jobs.usecases.process_upload.usecase.provide_get_card",
            ) as mock_provide_get_card,
        ):
            mock_get_card = Mock()
            mock_get_card.execute = Mock(return_value=mock_card)
            mock_provide_get_card.return_value = mock_get_card

            mock_extraction_service.extract_statement.side_effect = Exception(
                "Unexpected error"
            )

            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"test pdf",
                card_id=card_id,
                file_path="statements/test.pdf",
            )

            mock_session.close.assert_called_once()


class TestApplyRules:
    """Test suite for rules application."""

    def test_apply_rules_to_statement_success(self, mock_session):
        """Given: valid statement with transactions
        When: _apply_rules_to_statement() called
        Then: rules are applied and logged
        """
        user_id = uuid.uuid4()
        statement_id = uuid.uuid4()

        with patch(
            "app.domains.upload_jobs.usecases.process_upload.usecase.provide_apply_rules"
        ) as mock_provide:
            mock_apply_rules = Mock()
            mock_apply_rules.execute = Mock(
                return_value=ApplyRulesResponse(
                    transactions_processed=5,
                    tags_applied=3,
                    details=[],
                )
            )
            mock_provide.return_value = mock_apply_rules

            _apply_rules_to_statement(mock_session, user_id, statement_id)

            mock_apply_rules.execute.assert_called_once()

    def test_apply_rules_failure_non_blocking(self, mock_session):
        """Given: rules application fails
        When: _apply_rules_to_statement() called
        Then: failure is logged but not raised
        """
        user_id = uuid.uuid4()
        statement_id = uuid.uuid4()

        with patch(
            "app.domains.upload_jobs.usecases.process_upload.usecase.provide_apply_rules"
        ) as mock_provide:
            mock_apply_rules = Mock()
            mock_apply_rules.execute = Mock(side_effect=Exception("Rules engine down"))
            mock_provide.return_value = mock_apply_rules

            # Should not raise
            _apply_rules_to_statement(mock_session, user_id, statement_id)

            mock_apply_rules.execute.assert_called_once()
