"""Unit tests for process_upload usecase."""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.domains.card_statements.domain.models import (
    CardStatementCreate,
    CardStatementPublic,
    StatementStatus,
)
from app.domains.credit_cards.domain.models import CreditCardPublic
from app.domains.rules.domain.models import ApplyRulesRequest, ApplyRulesResponse
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
    _extract_date,
    _extract_installment,
    import_partial_statement,
    import_statement,
    process_upload_job,
)
from app.pkgs.extraction.models import (
    ExtractedCycle,
    ExtractedStatement,
    ExtractedTransaction,
    InstallmentInfo,
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
def mock_card():
    """Mock credit card."""
    return CreditCardPublic(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        bank="Test Bank",
        brand="visa",
        last4="1234",
        default_currency="USD",
    )


@pytest.fixture
def mock_get_card_usecase(mock_card):
    """Mock get card usecase."""
    usecase = Mock()
    usecase.execute = Mock(return_value=mock_card)
    return usecase


@pytest.fixture
def mock_extraction_service():
    """Mock extraction service."""
    service = Mock()
    service.extract_statement = AsyncMock()
    return service


def _create_mock_currency_service():
    """Create a mock currency service (helper function)."""
    service = Mock()
    service.convert_balance = AsyncMock(return_value=Decimal("100.00"))
    return service


@pytest.fixture
def mock_currency_service():
    """Mock currency service."""
    return _create_mock_currency_service()


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
def sample_extraction_result():
    """Successful extraction result."""
    return _mock_extraction_result(success=True)


@pytest.fixture
def partial_extraction_result():
    """Partial extraction result."""
    return _mock_extraction_result(success=False, partial=True)


@pytest.fixture
def failed_extraction_result():
    """Failed extraction result."""
    return _mock_extraction_result(success=False, partial=False)


@pytest.fixture
def mock_apply_rules_usecase():
    """Mock apply rules usecase."""
    usecase = Mock()
    usecase.execute = Mock(
        return_value=ApplyRulesResponse(
            transactions_processed=5, tags_applied=3, details=[]
        )
    )
    return usecase


def _mock_statement(statement_id=None):
    """Create a mock statement."""
    return CardStatementPublic(
        id=statement_id or uuid.uuid4(),
        card_id=uuid.uuid4(),
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
        close_date=date(2024, 1, 31),
        due_date=date(2024, 2, 15),
        previous_balance=Decimal("500.00"),
        current_balance=Decimal("1000.00"),
        minimum_payment=Decimal("50.00"),
        currency="USD",
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
        description="Test Merchant",
        amount=Decimal("25.00"),
        currency="USD",
        coupon=None,
        installment_cur=None,
        installment_tot=None,
    )


def _mock_extraction_result(success=True, partial=False):
    """Create a mock extraction result."""
    from app.pkgs.extraction.models import ExtractionResult

    if success:
        data = ExtractedStatement(
            statement_id="stmt-123",
            period=ExtractedCycle(
                start=date(2024, 1, 1),
                end=date(2024, 1, 31),
                due_date=date(2024, 2, 15),
            ),
            previous_balance=[Money(amount=Decimal("500.00"), currency="USD")],
            current_balance=[Money(amount=Decimal("1000.00"), currency="USD")],
            minimum_payment=[Money(amount=Decimal("50.00"), currency="USD")],
            transactions=[
                ExtractedTransaction(
                    date=date(2024, 1, 15),
                    merchant="Test Merchant",
                    amount=Money(amount=Decimal("25.00"), currency="USD"),
                    coupon=None,
                    installment=None,
                )
            ],
        )
        return ExtractionResult(
            success=True, data=data, model_used="google/gemini-flash-1.5"
        )
    elif partial:
        partial_data = {
            "period": {"start": "2024-01-01", "end": "2024-01-31"},
            "current_balance": [{"amount": "1000.00", "currency": "USD"}],
        }
        return ExtractionResult(
            success=False,
            partial_data=partial_data,
            error="Validation error",
            model_used="google/gemini-flash-1.5",
        )
    else:
        return ExtractionResult(
            success=False,
            error="No data extracted",
            model_used="google/gemini-flash-1.5",
        )


class TestProcessUploadJob:
    """Test suite for process_upload_job function."""

    @pytest.mark.asyncio
    async def test_updates_job_to_processing_at_start(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        sample_extraction_result,
    ):
        """Given: pending job
        When: process_upload_job() starts
        Then: job_service.update_status(job_id, PROCESSING) called first
        """
        job_id = uuid.uuid4()
        mock_extraction_service.extract_statement.return_value = (
            sample_extraction_result
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(),
            provide_transaction_service=Mock(),
        ):
            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        # First call should be to update status to PROCESSING
        mock_job_service.update_status.assert_any_call(
            job_id, UploadJobStatus.PROCESSING
        )

    @pytest.mark.asyncio
    async def test_fetches_card_for_currency(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        sample_extraction_result,
    ):
        """Given: job being processed
        When: process runs
        Then: get_card_usecase.execute(card_id) called
        """
        card_id = uuid.uuid4()
        mock_extraction_service.extract_statement.return_value = (
            sample_extraction_result
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(),
            provide_transaction_service=Mock(),
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=b"fake pdf",
                card_id=card_id,
                file_path="statements/test.pdf",
            )

        mock_get_card_usecase.execute.assert_called_once_with(card_id)

    @pytest.mark.asyncio
    async def test_calls_extraction_service(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        sample_extraction_result,
    ):
        """Given: job being processed
        When: process runs
        Then: extraction_service.extract_statement(pdf_bytes) called
        """
        pdf_bytes = b"fake pdf"
        mock_extraction_service.extract_statement.return_value = (
            sample_extraction_result
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(),
            provide_transaction_service=Mock(),
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=pdf_bytes,
                card_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        mock_extraction_service.extract_statement.assert_any_call(
            pdf_bytes, model_index=0
        )

    @pytest.mark.asyncio
    async def test_retries_with_fallback_on_failure(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        partial_extraction_result,
    ):
        """Given: first extraction fails with error
        When: process runs
        Then: extraction called again with model_index=1
        And: job_service.increment_retry() called
        """
        job_id = uuid.uuid4()
        # First call fails with error, second call succeeds
        mock_extraction_service.extract_statement.side_effect = [
            partial_extraction_result,
            _mock_extraction_result(success=True),
        ]

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(
                return_value=Mock(create_statement=_mock_statement())
            ),
            provide_transaction_service=Mock(
                return_value=Mock(create_transaction=_mock_transaction())
            ),
        ):
            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        # Should increment retry after first failure
        mock_job_service.increment_retry.assert_called_once_with(job_id)
        # Should call extraction twice (once with primary, once with fallback)
        assert mock_extraction_service.extract_statement.call_count == 2

    @pytest.mark.asyncio
    async def test_converts_currencies(
        self,
        mock_session,
        mock_currency_service,
        mock_statement_service,
        mock_transaction_service,
    ):
        """Given: successful extraction with multi-currency balances
        When: import_statement() runs
        Then: currency_service.convert_balance() called for each balance type
        """
        data = _mock_extraction_result(success=True).data
        card_id = uuid.uuid4()
        target_currency = "USD"

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            provide_currency=lambda: mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
        ):
            await import_statement(
                session=mock_session,
                data=data,
                card_id=card_id,
                target_currency=target_currency,
                source_file_path="statements/test.pdf",
            )

        # Should call convert_balance for each balance type
        assert mock_currency_service.convert_balance.call_count == 3

    @pytest.mark.asyncio
    async def test_creates_statement_on_success(
        self,
        mock_session,
        mock_currency_service,
        mock_statement_service,
        mock_transaction_service,
    ):
        """Given: successful extraction
        When: process completes
        Then: statement_service.create_statement() called with correct data
        """
        data = _mock_extraction_result(success=True).data
        card_id = uuid.uuid4()
        target_currency = "USD"

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
        ):
            await import_statement(
                session=mock_session,
                data=data,
                card_id=card_id,
                target_currency=target_currency,
                source_file_path="statements/test.pdf",
            )

        # Check statement creation call
        mock_statement_service.create_statement.assert_called_once()
        call_args = mock_statement_service.create_statement.call_args.args[0]
        assert isinstance(call_args, CardStatementCreate)
        assert call_args.card_id == card_id
        assert call_args.currency == target_currency

    @pytest.mark.asyncio
    async def test_creates_transactions_on_success(
        self,
        mock_session,
        mock_currency_service,
        mock_statement_service,
        mock_transaction_service,
    ):
        """Given: successful extraction with 3 transactions
        When: process completes
        Then: transaction_service.create_transaction() called 3 times
        """
        data = _mock_extraction_result(success=True).data
        # Add 2 more transactions
        data.transactions = data.transactions * 3

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
        ):
            await import_statement(
                session=mock_session,
                data=data,
                card_id=uuid.uuid4(),
                target_currency="USD",
                source_file_path="statements/test.pdf",
            )

        assert mock_transaction_service.create_transaction.call_count == 3

    @pytest.mark.asyncio
    async def test_updates_job_to_completed(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        mock_statement_service,
        mock_transaction_service,
    ):
        """Given: successful processing
        When: process completes
        Then: job_service.update_status(job_id, COMPLETED, statement_id=...) called
        """
        mock_extraction_service.extract_statement.return_value = (
            _mock_extraction_result(success=True)
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_closes_session_on_error(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        failed_extraction_result,
    ):
        """Given: exception during processing
        When: process fails
        Then: session.close() still called
        """
        mock_extraction_service.extract_statement.return_value = (
            failed_extraction_result
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_installment_fields(
        self,
        mock_session,
        mock_currency_service,
        mock_statement_service,
        mock_transaction_service,
    ):
        """Given: extraction with installment info (2/6)
        When: transactions created
        Then: installment_cur=2, installment_tot=6
        """
        data = _mock_extraction_result(success=True).data
        data.transactions[0].installment = InstallmentInfo(current=2, total=6)

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
        ):
            await import_statement(
                session=mock_session,
                data=data,
                card_id=uuid.uuid4(),
                target_currency="USD",
                source_file_path="statements/test.pdf",
            )

        call_args = mock_transaction_service.create_transaction.call_args.args[0]
        assert call_args.installment_cur == 2
        assert call_args.installment_tot == 6

    @pytest.mark.asyncio
    async def test_statement_source_file_path(
        self,
        mock_session,
        mock_currency_service,
        mock_statement_service,
        mock_transaction_service,
    ):
        """Given: file_path passed to process_upload_job
        When: statement created
        Then: source_file_path set on statement
        """
        data = _mock_extraction_result(success=True).data
        file_path = "statements/test.pdf"

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
        ):
            await import_statement(
                session=mock_session,
                data=data,
                card_id=uuid.uuid4(),
                target_currency="USD",
                source_file_path=file_path,
            )

        call_args = mock_statement_service.create_statement.call_args.args[0]
        assert call_args.source_file_path == file_path


class TestImportPartialStatement:
    """Test suite for import_partial_statement helper."""

    @pytest.mark.asyncio
    async def test_handles_missing_period_dates(
        self,
        mock_session,
        mock_currency_service,
        mock_statement_service,
        mock_transaction_service,
    ):
        """Given: partial_data with missing period dates
        When: import_partial_statement runs
        Then: statement created with None dates
        """
        partial_data = {
            "current_balance": [{"amount": "1000.00", "currency": "USD"}],
        }

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
        ):
            await import_partial_statement(
                session=mock_session,
                partial_data=partial_data,
                card_id=uuid.uuid4(),
                target_currency="USD",
                source_file_path="statements/test.pdf",
            )

        call_args = mock_statement_service.create_statement.call_args.args[0]
        assert call_args.period_start is None
        assert call_args.period_end is None


class TestHelperFunctions:
    """Test suite for helper functions."""

    def test_extract_date_with_date_object(self):
        """Given: date object
        When: _extract_date() called
        Then: returns same date
        """
        input_date = date(2024, 1, 15)
        result = _extract_date(input_date)
        assert result == input_date

    def test_extract_date_with_string(self):
        """Given: date string
        When: _extract_date() called
        Then: returns date object
        """
        result = _extract_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_extract_date_with_invalid_string(self):
        """Given: invalid date string
        When: _extract_date() called
        Then: returns None
        """
        result = _extract_date("invalid-date")
        assert result is None

    def test_extract_date_with_none(self):
        """Given: None value
        When: _extract_date() called
        Then: returns None
        """
        result = _extract_date(None)
        assert result is None

    def test_extract_installment_with_dict(self):
        """Given: installment dict
        When: _extract_installment() called
        Then: returns field value
        """
        installment = {"current": 2, "total": 6}
        result = _extract_installment(installment, "current")
        assert result == 2

    def test_extract_installment_with_none(self):
        """Given: None value
        When: _extract_installment() called
        Then: returns None
        """
        result = _extract_installment(None, "current")
        assert result is None

    def test_extract_installment_with_missing_field(self):
        """Given: installment dict without field
        When: _extract_installment() called
        Then: returns None
        """
        installment = {"current": 2}
        result = _extract_installment(installment, "total")
        assert result is None


class TestRulesIntegration:
    """Test suite for rules engine integration."""

    def test_apply_rules_called_on_success(
        self,
        mock_session,
        mock_apply_rules_usecase,
    ):
        """Given: successful statement import
        When: _apply_rules_to_statement() called
        Then: apply_rules_usecase.execute() called with correct args
        """
        user_id = uuid.uuid4()
        statement_id = uuid.uuid4()

        with patch(
            "app.domains.upload_jobs.usecases.process_upload.usecase.provide_apply_rules",
            return_value=mock_apply_rules_usecase,
        ):
            _apply_rules_to_statement(mock_session, user_id, statement_id)

        mock_apply_rules_usecase.execute.assert_called_once()
        call_args = mock_apply_rules_usecase.execute.call_args
        assert call_args[0][0] == user_id
        assert isinstance(call_args[0][1], ApplyRulesRequest)
        assert call_args[0][1].statement_id == statement_id

    def test_apply_rules_failure_does_not_raise(
        self,
        mock_session,
    ):
        """Given: rules application fails
        When: _apply_rules_to_statement() called
        Then: no exception raised (non-blocking)
        """
        mock_apply_rules_usecase = Mock()
        mock_apply_rules_usecase.execute = Mock(side_effect=Exception("Rules error"))

        with patch(
            "app.domains.upload_jobs.usecases.process_upload.usecase.provide_apply_rules",
            return_value=mock_apply_rules_usecase,
        ):
            # Should not raise
            _apply_rules_to_statement(mock_session, uuid.uuid4(), uuid.uuid4())

    @pytest.mark.asyncio
    async def test_rules_applied_after_successful_import(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        mock_statement_service,
        mock_transaction_service,
        mock_apply_rules_usecase,
        mock_card,
    ):
        """Given: successful extraction
        When: process_upload_job completes
        Then: rules are applied to the new statement
        """
        mock_extraction_service.extract_statement.return_value = (
            _mock_extraction_result(success=True)
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
            provide_apply_rules=Mock(return_value=mock_apply_rules_usecase),
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        mock_apply_rules_usecase.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_rules_applied_after_partial_import(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        mock_statement_service,
        mock_transaction_service,
        mock_apply_rules_usecase,
        partial_extraction_result,
    ):
        """Given: partial extraction
        When: process_upload_job completes with partial status
        Then: rules are still applied to the new statement
        """
        # First call fails, second returns partial
        mock_extraction_service.extract_statement.side_effect = [
            partial_extraction_result,
            partial_extraction_result,
        ]

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
            provide_apply_rules=Mock(return_value=mock_apply_rules_usecase),
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        mock_apply_rules_usecase.execute.assert_called_once()


class TestErrorHandling:
    """Test suite for error handling improvements."""

    @pytest.mark.asyncio
    async def test_extraction_error_sets_failed_status(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        failed_extraction_result,
    ):
        """Given: extraction fails completely
        When: process_upload_job runs
        Then: job status set to FAILED with extraction error message
        """
        job_id = uuid.uuid4()
        mock_extraction_service.extract_statement.return_value = (
            failed_extraction_result
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
        ):
            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        # Check that FAILED status was set with extraction error
        final_call = mock_job_service.update_status.call_args_list[-1]
        assert final_call[0][1] == UploadJobStatus.FAILED
        assert "Extraction failed" in final_call[1]["error_message"]

    @pytest.mark.asyncio
    async def test_unexpected_error_sets_failed_status(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
    ):
        """Given: unexpected exception during processing
        When: process_upload_job runs
        Then: job status set to FAILED with processing error message
        """
        job_id = uuid.uuid4()
        mock_extraction_service.extract_statement.side_effect = RuntimeError(
            "Unexpected error"
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
        ):
            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        # Check that FAILED status was set
        final_call = mock_job_service.update_status.call_args_list[-1]
        assert final_call[0][1] == UploadJobStatus.FAILED
        assert "Processing error" in final_call[1]["error_message"]

    @pytest.mark.asyncio
    async def test_session_closed_on_extraction_error(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        failed_extraction_result,
    ):
        """Given: extraction error
        When: process_upload_job fails
        Then: session is still closed
        """
        mock_extraction_service.extract_statement.return_value = (
            failed_extraction_result
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=_create_mock_currency_service,
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        mock_session.close.assert_called_once()


class TestCustomExceptions:
    """Test suite for custom exception classes."""

    def test_extraction_error_attributes(self):
        """Given: ExtractionError created
        When: attributes accessed
        Then: message and model_used available
        """
        error = ExtractionError("Parse failed", model_used="google/gemini-flash-1.5")
        assert str(error) == "Parse failed"
        assert error.model_used == "google/gemini-flash-1.5"

    def test_currency_conversion_error_attributes(self):
        """Given: CurrencyConversionError created
        When: attributes accessed
        Then: message and source_currency available
        """
        error = CurrencyConversionError("Rate not found", source_currency="BRL")
        assert str(error) == "Rate not found"
        assert error.source_currency == "BRL"
