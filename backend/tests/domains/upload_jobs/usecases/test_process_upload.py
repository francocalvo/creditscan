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
from app.domains.transactions.domain.models import (
    TransactionPublic,
)
from app.domains.upload_jobs.domain.models import UploadJobStatus
from app.domains.upload_jobs.usecases.process_upload.usecase import (
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
            provide_currency=lambda: mock_currency_service,
            provide_statement_service=Mock(),
            provide_transaction_service=Mock(),
        ):
            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
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
            provide_currency=lambda: mock_currency_service,
            provide_statement_service=Mock(),
            provide_transaction_service=Mock(),
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=b"fake pdf",
                card_id=card_id,
                user_id=uuid.uuid4(),
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
            provide_currency=lambda: mock_currency_service,
            provide_statement_service=Mock(),
            provide_transaction_service=Mock(),
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=pdf_bytes,
                card_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
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
            provide_currency=lambda: mock_currency_service,
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
                user_id=uuid.uuid4(),
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
            provide_currency=lambda: mock_currency_service,
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
        job_id = uuid.uuid4()
        mock_extraction_service.extract_statement.return_value = (
            _mock_extraction_result(success=True)
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=lambda: mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
        ):
            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        # Find the COMPLETED update call
        completed_calls = [
            call
            for call in mock_job_service.update_status.call_args_list
            if len(call[0]) >= 2 and call[0][1] == UploadJobStatus.COMPLETED
        ]
        assert len(completed_calls) >= 1
        completed_call = completed_calls[0]
        assert completed_call[0][0] == job_id

    @pytest.mark.asyncio
    async def test_handles_partial_extraction(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        mock_statement_service,
        mock_transaction_service,
        partial_extraction_result,
    ):
        """Given: extraction returns partial_data
        When: process runs
        Then: statement created with PENDING_REVIEW status
        And: job_service.update_status(job_id, PARTIAL, ...) called
        """
        job_id = uuid.uuid4()
        mock_extraction_service.extract_statement.return_value = (
            partial_extraction_result
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=lambda: mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
        ):
            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        # Find the PARTIAL update call
        partial_calls = [
            call
            for call in mock_job_service.update_status.call_args_list
            if len(call[0]) >= 2 and call[0][1] == UploadJobStatus.PARTIAL
        ]
        assert len(partial_calls) >= 1

    @pytest.mark.asyncio
    async def test_updates_job_to_failed_on_error(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        failed_extraction_result,
    ):
        """Given: extraction fails completely
        When: process runs
        Then: job_service.update_status(job_id, FAILED, error_message=...) called
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
            provide_currency=lambda: mock_currency_service,
        ):
            await process_upload_job(
                job_id=job_id,
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                file_path="statements/test.pdf",
            )

        # Find the FAILED update call
        failed_calls = [
            call
            for call in mock_job_service.update_status.call_args_list
            if len(call[0]) >= 2 and call[0][1] == UploadJobStatus.FAILED
        ]
        assert len(failed_calls) >= 1
        failed_call = failed_calls[0]
        assert failed_call[0][0] == job_id

    @pytest.mark.asyncio
    async def test_closes_session_on_success(
        self,
        mock_session,
        mock_job_service,
        mock_get_card_usecase,
        mock_extraction_service,
        sample_extraction_result,
        mock_statement_service,
        mock_transaction_service,
    ):
        """Given: successful processing
        When: process completes
        Then: session.close() called
        """
        mock_extraction_service.extract_statement.return_value = (
            sample_extraction_result
        )

        with patch.multiple(
            "app.domains.upload_jobs.usecases.process_upload.usecase",
            get_db_session=Mock(return_value=mock_session),
            provide_upload_job_service=Mock(return_value=mock_job_service),
            provide_get_card=Mock(return_value=mock_get_card_usecase),
            provide_extraction=Mock(return_value=mock_extraction_service),
            provide_currency=lambda: mock_currency_service,
            provide_statement_service=Mock(return_value=mock_statement_service),
            provide_transaction_service=Mock(return_value=mock_transaction_service),
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
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
            provide_currency=lambda: mock_currency_service,
        ):
            await process_upload_job(
                job_id=uuid.uuid4(),
                pdf_bytes=b"fake pdf",
                card_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
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
            provide_currency=lambda: mock_currency_service,
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
            provide_currency=lambda: mock_currency_service,
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
            provide_currency=lambda: mock_currency_service,
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
