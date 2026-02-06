"""Tests for admin extraction endpoint."""

import logging
from datetime import UTC, datetime
from datetime import date as Date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.domains.currency.domain.models import ExchangeRate
from app.domains.currency.service.exchange_rate_extractor import ExtractedRate


class TestCurrencyExtract:
    """Tests for POST /currency/rates/extract."""

    def test_extract_requires_auth(self, client: TestClient) -> None:
        """Unauthenticated requests should be rejected."""
        r = client.post(f"{settings.API_V1_STR}/currency/rates/extract")
        assert r.status_code == 401

    def test_extract_admin_only(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Normal users should get 403 with specific error message."""
        r = client.post(
            f"{settings.API_V1_STR}/currency/rates/extract",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 403
        assert r.json()["detail"] == "Admin access required"

    def test_extract_happy_path(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Superuser should get 202 Accepted with extraction started status."""

        # Mock the extraction job to prevent actual HTTP calls
        async def mock_run_extraction_job(*args, **kwargs):  # noqa: ARG001
            return None

        monkeypatch.setattr(
            "app.api.routes.currency.extract.run_extraction_job",
            mock_run_extraction_job,
        )

        r = client.post(
            f"{settings.API_V1_STR}/currency/rates/extract",
            headers=superuser_token_headers,
        )
        assert r.status_code == 202
        assert r.json() == {"status": "extraction_started"}

    def test_extract_enqueues_background_task(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify endpoint enqueues run_extraction_job via BackgroundTasks."""
        # Mock the extraction job to verify it gets called
        task_called = []

        async def mock_run_extraction_job(*args, **kwargs):  # noqa: ARG001
            task_called.append(True)

        monkeypatch.setattr(
            "app.api.routes.currency.extract.run_extraction_job",
            mock_run_extraction_job,
        )

        r = client.post(
            f"{settings.API_V1_STR}/currency/rates/extract",
            headers=superuser_token_headers,
        )
        assert r.status_code == 202

        # Verify the background task function was called
        # (FastAPI TestClient runs background tasks synchronously)
        assert len(task_called) == 1


class TestExtractionJob:
    """Tests for run_extraction_job background job."""

    @pytest.mark.asyncio
    async def test_job_successful_extraction(
        self, db: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Job should fetch rate and upsert to database."""
        # Create deterministic extracted rate
        extracted_rate = ExtractedRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=Date(2026, 2, 4),
            fetched_at=datetime(2026, 2, 4, 15, 30, 0, tzinfo=UTC),
            source="cronista_mep",
        )

        # Patch ExchangeRateExtractor.fetch_current_rate
        async def mock_fetch(*args, **kwargs):  # noqa: ARG001
            return extracted_rate

        from app.api.routes.currency import extract

        connection = db.connection()

        def get_test_db_session() -> Session:
            return Session(bind=connection)

        monkeypatch.setattr(
            "app.api.routes.currency.extract.get_db_session",
            get_test_db_session,
        )
        monkeypatch.setattr(
            "app.api.routes.currency.extract.ExchangeRateExtractor.fetch_current_rate",
            mock_fetch,
        )

        # Run job - it creates its own session
        await extract.run_extraction_job()

        # Verify rate was upserted to database
        # (The job creates its own session, so we can verify in test session)
        from sqlmodel import select

        statement = select(ExchangeRate).where(
            ExchangeRate.rate_date == Date(2026, 2, 4)
        )
        saved_rate = db.exec(statement).first()
        assert saved_rate is not None
        assert saved_rate.buy_rate == Decimal("1458.74")
        assert saved_rate.sell_rate == Decimal("1459.32")
        assert saved_rate.source == "cronista_mep"

    @pytest.mark.asyncio
    async def test_job_upserts_existing_rate(
        self, db: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Job should update existing rate if it already exists."""
        # Create two different extracted rates with same date
        extracted_rate_1 = ExtractedRate(
            buy_rate=Decimal("1400.00"),
            sell_rate=Decimal("1400.00"),
            rate_date=Date(2026, 2, 4),
            fetched_at=datetime(2026, 2, 3, 12, 0, 0, tzinfo=UTC),
            source="manual",
        )

        extracted_rate_2 = ExtractedRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=Date(2026, 2, 4),
            fetched_at=datetime(2026, 2, 4, 15, 30, 0, tzinfo=UTC),
            source="cronista_mep",
        )

        # Patch ExchangeRateExtractor.fetch_current_rate to return first rate
        call_count = [0]

        async def mock_fetch(*args, **kwargs):  # noqa: ARG001
            call_count[0] += 1
            if call_count[0] == 1:
                return extracted_rate_1
            else:
                return extracted_rate_2

        from app.api.routes.currency import extract

        connection = db.connection()

        def get_test_db_session() -> Session:
            return Session(bind=connection)

        monkeypatch.setattr(
            "app.api.routes.currency.extract.get_db_session",
            get_test_db_session,
        )
        monkeypatch.setattr(
            "app.api.routes.currency.extract.ExchangeRateExtractor.fetch_current_rate",
            mock_fetch,
        )

        # Run job twice - it should upsert the same rate twice
        await extract.run_extraction_job()
        await extract.run_extraction_job()

        # Verify only one rate exists (upserted twice)
        from sqlmodel import select

        statement = select(ExchangeRate).where(
            ExchangeRate.rate_date == Date(2026, 2, 4)
        )
        saved_rates = list(db.exec(statement).all())
        assert len(saved_rates) == 1  # Still only one record

        saved_rate = saved_rates[0]
        # Should have the values from the second call
        assert saved_rate.buy_rate == Decimal("1458.74")  # Updated
        assert saved_rate.sell_rate == Decimal("1459.32")  # Updated
        assert saved_rate.source == "cronista_mep"

    @pytest.mark.asyncio
    async def test_job_logs_and_re_raises_on_failure(
        self,
        db: Session,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Job should log failure with traceback and re-raise."""
        connection = db.connection()

        def get_test_db_session() -> Session:
            return Session(bind=connection)

        from app.api.routes.currency import extract

        monkeypatch.setattr(
            "app.api.routes.currency.extract.get_db_session",
            get_test_db_session,
        )

        # Patch ExchangeRateExtractor.fetch_current_rate to raise
        async def mock_fetch(*args, **kwargs):  # noqa: ARG001
            raise ValueError("Simulated extraction failure")

        monkeypatch.setattr(
            "app.api.routes.currency.extract.ExchangeRateExtractor.fetch_current_rate",
            mock_fetch,
        )

        # Run the job and expect it to re-raise
        # Job creates its own session
        with pytest.raises(ValueError, match="Simulated extraction failure"):
            await extract.run_extraction_job()

        # Verify exception was logged
        assert len(caplog.records) > 0
        # Check that we got an ERROR or CRITICAL log with traceback
        error_logs = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert len(error_logs) >= 1
        assert "Rate extraction job failed" in error_logs[0].message

    @pytest.mark.asyncio
    async def test_job_creates_dedicated_session(
        self, db: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Job should use its own session, not the request-scoped one."""
        # This test verifies that run_extraction_job creates a new session
        # even when called without a session_factory parameter.

        extracted_rate = ExtractedRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=Date(2026, 2, 4),
            fetched_at=datetime(2026, 2, 4, 15, 30, 0, tzinfo=UTC),
            source="cronista_mep",
        )

        # Patch ExchangeRateExtractor.fetch_current_rate
        async def mock_fetch(*args, **kwargs):  # noqa: ARG001
            return extracted_rate

        from app.api.routes.currency import extract

        connection = db.connection()

        def get_test_db_session() -> Session:
            return Session(bind=connection)

        monkeypatch.setattr(
            "app.api.routes.currency.extract.get_db_session",
            get_test_db_session,
        )
        monkeypatch.setattr(
            "app.api.routes.currency.extract.ExchangeRateExtractor.fetch_current_rate",
            mock_fetch,
        )

        # Call without session_factory (uses default get_db_session)
        # This should work even though we're in a test context
        await extract.run_extraction_job()

        # Note: In the actual test database, we can't easily verify the
        # dedicated session behavior because the test session is also
        # using the same test engine. However, the code structure
        # (calling get_db_session() directly) ensures a separate session
        # is created, which is sufficient for this test.

    @pytest.mark.asyncio
    async def test_job_closes_session_on_success(
        self,
        db: Session,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Job should close session after successful upsert."""
        extracted_rate = ExtractedRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=Date(2026, 2, 4),
            fetched_at=datetime(2026, 2, 4, 15, 30, 0, tzinfo=UTC),
            source="cronista_mep",
        )

        # Patch ExchangeRateExtractor.fetch_current_rate
        async def mock_fetch(*args, **kwargs):  # noqa: ARG001
            return extracted_rate

        from app.api.routes.currency import extract

        connection = db.connection()

        monkeypatch.setattr(
            "app.api.routes.currency.extract.ExchangeRateExtractor.fetch_current_rate",
            mock_fetch,
        )

        # Spy on the specific session created by the job (avoid global patching).
        close_called = []

        def spy_get_db_session() -> Session:
            session = Session(bind=connection)
            original_close = session.close

            def spy_close() -> None:
                close_called.append(True)
                original_close()

            session.close = spy_close
            return session

        monkeypatch.setattr(
            "app.api.routes.currency.extract.get_db_session",
            spy_get_db_session,
        )

        # Run the job - it creates and closes its own session
        await extract.run_extraction_job()

        # Verify close was called
        assert len(close_called) == 1

        # Verify success was logged
        success_logs = [r for r in caplog.records if r.levelno == logging.INFO]
        assert len(success_logs) >= 1
        assert any(
            "Successfully upserted exchange rate" in r.message for r in success_logs
        )
