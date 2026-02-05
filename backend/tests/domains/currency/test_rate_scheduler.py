"""Tests for rate extraction scheduler."""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.currency.domain.models import ExchangeRate
from app.domains.currency.service.exchange_rate_extractor import ExtractedRate
from app.domains.currency.service.rate_scheduler import RateExtractionScheduler


class TestRateExtractionScheduler:
    """Test RateExtractionScheduler."""

    def test_next_run_time_same_day(self) -> None:
        """Test calculation of next run time when it's earlier today."""
        scheduler = RateExtractionScheduler(hour=21, minute=0)
        # 15:00 UTC
        now = datetime(2025, 2, 4, 15, 0, 0, tzinfo=UTC)

        next_run = scheduler._next_run_time(now)

        assert next_run == datetime(2025, 2, 4, 21, 0, 0, tzinfo=UTC)

    def test_next_run_time_next_day(self) -> None:
        """Test calculation of next run time when it's already passed today."""
        scheduler = RateExtractionScheduler(hour=21, minute=0)
        # 22:00 UTC
        now = datetime(2025, 2, 4, 22, 0, 0, tzinfo=UTC)

        next_run = scheduler._next_run_time(now)

        assert next_run == datetime(2025, 2, 5, 21, 0, 0, tzinfo=UTC)

    def test_next_run_time_exact_match(self) -> None:
        """Test calculation of next run time when it's exactly now (should be tomorrow)."""
        scheduler = RateExtractionScheduler(hour=21, minute=0)
        # 21:00 UTC exactly
        now = datetime(2025, 2, 4, 21, 0, 0, tzinfo=UTC)

        next_run = scheduler._next_run_time(now)

        assert next_run == datetime(2025, 2, 5, 21, 0, 0, tzinfo=UTC)

    def test_start_stop(self) -> None:
        """Test that start() creates a task and stop() cancels it."""
        scheduler = RateExtractionScheduler()

        with patch("asyncio.create_task") as mock_create_task:
            # Create a real future to avoid "can't be used in await expression"
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            task = loop.create_future()
            mock_create_task.return_value = task
            scheduler.start()
            assert scheduler._running is True
            mock_create_task.assert_called_once()
            scheduler._task = task

        async def mock_stop():
            # In a real scenario, cancel() makes the task raise CancelledError when awaited
            task.cancel = MagicMock()
            # Simulate the task finishing with CancelledError
            task.set_exception(asyncio.CancelledError())
            await scheduler.stop()

        asyncio.run(mock_stop())
        assert scheduler._running is False
        task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_extraction_success(self) -> None:
        """Test successful execution of one extraction run."""
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)

        mock_extractor = AsyncMock()
        mock_extracted_rate = ExtractedRate(
            buy_rate=Decimal("1000.00"),
            sell_rate=Decimal("1100.00"),
            rate_date=datetime(2025, 2, 4).date(),
            fetched_at=datetime(2025, 2, 4, 21, 0, 0, tzinfo=UTC),
            source="cronista_mep",
        )
        mock_extractor.fetch_current_rate.return_value = mock_extracted_rate
        mock_extractor_factory = MagicMock(return_value=mock_extractor)

        mock_repository = MagicMock()
        mock_repository_provider = MagicMock(return_value=mock_repository)

        scheduler = RateExtractionScheduler(
            session_factory=mock_session_factory,
            extractor_factory=mock_extractor_factory,
            repository_provider=mock_repository_provider,
        )

        await scheduler._execute_extraction()

        mock_session_factory.assert_called_once()
        mock_extractor_factory.assert_called_once()
        mock_repository_provider.assert_called_once_with(mock_session)

        mock_extractor.fetch_current_rate.assert_called_once()

        # Verify upsert_rate was called with correct ExchangeRate object
        mock_repository.upsert_rate.assert_called_once()
        call_args = mock_repository.upsert_rate.call_args
        passed_session, passed_rate = call_args[0]

        assert passed_session == mock_session
        assert isinstance(passed_rate, ExchangeRate)
        assert passed_rate.rate_date == mock_extracted_rate.rate_date
        assert passed_rate.buy_rate == mock_extracted_rate.buy_rate
        assert passed_rate.sell_rate == mock_extracted_rate.sell_rate

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_loop_execution_and_failure_resilience(self) -> None:
        """Test that loop continues even if extraction fails once."""
        scheduler = RateExtractionScheduler()
        scheduler._running = True

        # Mock _next_run_time to return "now" so it triggers immediately
        # and then return a far future time to stop the loop (or we can manually stop it)
        now = datetime.now(UTC)
        scheduler._next_run_time = MagicMock(
            side_effect=[now, now + timedelta(hours=1)]
        )

        # Mock asyncio.sleep to return immediately
        with patch("asyncio.sleep", AsyncMock()):
            # Mock _execute_extraction to fail once then succeed
            with patch.object(
                scheduler, "_execute_extraction", AsyncMock()
            ) as mock_execute:
                side_effects = [Exception("First run failed"), None]

                async def wrapper_execute():
                    if not side_effects:
                        scheduler._running = False
                        return
                    effect = side_effects.pop(0)
                    if not side_effects:
                        scheduler._running = False
                    if isinstance(effect, Exception):
                        raise effect
                    return effect

                mock_execute.side_effect = wrapper_execute

                await scheduler._run_loop()

                assert mock_execute.call_count == 2
                # Loop continued after first failure
