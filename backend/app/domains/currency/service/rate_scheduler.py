"""Asyncio scheduler for daily exchange rate extraction."""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, time, timedelta
from typing import Any

from sqlmodel import Session

from app.domains.currency.domain.models import ExchangeRate
from app.domains.currency.repository.exchange_rate_repository import (
    ExchangeRateRepository,
)
from app.domains.currency.repository.exchange_rate_repository import (
    provide as provide_repository,
)
from app.domains.currency.service.exchange_rate_extractor import ExchangeRateExtractor
from app.pkgs.database import get_db_session

logger = logging.getLogger(__name__)


class RateExtractionScheduler:
    """Scheduler for periodic exchange rate extraction."""

    def __init__(
        self,
        hour: int = 21,
        minute: int = 0,
        session_factory: Callable[[], Session] = get_db_session,
        extractor_factory: Callable[[], ExchangeRateExtractor] = ExchangeRateExtractor,
        repository_provider: Callable[
            [Session], ExchangeRateRepository
        ] = provide_repository,
    ) -> None:
        """Initialize scheduler.

        Args:
            hour: UTC hour to run extraction (default: 21)
            minute: UTC minute to run extraction (default: 0)
            session_factory: Callable that returns a new DB session
            extractor_factory: Callable that returns an extractor instance
            repository_provider: Callable that returns a repository instance for a session
        """
        self.scheduled_time = time(hour=hour, minute=minute)
        self.session_factory = session_factory
        self.extractor_factory = extractor_factory
        self.repository_provider = repository_provider
        self._task: asyncio.Task[Any] | None = None
        self._running = False

    def start(self) -> None:
        """Start the scheduler in the background."""
        if self._running:
            logger.warning("RateExtractionScheduler is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"RateExtractionScheduler started, scheduled for {self.scheduled_time} UTC daily"
        )

    async def stop(self) -> None:
        """Stop the scheduler and wait for task completion."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("RateExtractionScheduler stopped")

    def _next_run_time(self, now: datetime | None = None) -> datetime:
        """Calculate the next run time in UTC.

        Args:
            now: Current time (defaults to datetime.now(UTC))

        Returns:
            Next occurrence of scheduled_time in UTC
        """
        if now is None:
            now = datetime.now(UTC)

        next_run = datetime.combine(now.date(), self.scheduled_time, tzinfo=UTC)

        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run

    async def _run_loop(self) -> None:
        """Background loop that waits and executes extraction."""
        while self._running:
            next_run = self._next_run_time()
            sleep_seconds = (next_run - datetime.now(UTC)).total_seconds()

            if sleep_seconds > 0:
                logger.info(
                    f"Next rate extraction at {next_run} UTC (in {sleep_seconds:.1f} seconds)"
                )
                try:
                    await asyncio.sleep(sleep_seconds)
                except asyncio.CancelledError:
                    break

            if not self._running:
                break

            logger.info("Starting scheduled rate extraction")
            try:
                await self._execute_extraction()
                logger.info("Scheduled rate extraction completed successfully")
            except Exception:
                logger.exception("Scheduled rate extraction failed")

    async def _execute_extraction(self) -> None:
        """Perform one extraction run."""
        session = self.session_factory()
        try:
            extractor = self.extractor_factory()
            repository = self.repository_provider(session)

            extracted_rate = await extractor.fetch_current_rate()

            exchange_rate = ExchangeRate(
                rate_date=extracted_rate.rate_date,
                buy_rate=extracted_rate.buy_rate,
                sell_rate=extracted_rate.sell_rate,
                source=extracted_rate.source,
                fetched_at=extracted_rate.fetched_at,
            )

            repository.upsert_rate(session, exchange_rate)
            session.commit()
        finally:
            session.close()
