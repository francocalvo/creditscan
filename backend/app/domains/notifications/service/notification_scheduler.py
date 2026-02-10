"""Asyncio scheduler for daily due date notifications."""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, time, timedelta
from typing import Any

from sqlmodel import Session

from app.domains.notifications.service.ntfy_client import NtfyClient
from app.domains.notifications.usecases.send_due_notifications.usecase import provide
from app.pkgs.database import get_db_session

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """Scheduler for periodic due date notification checks."""

    def __init__(
        self,
        hour: int = 22,
        minute: int = 0,
        session_factory: Callable[[], Session] = get_db_session,
        ntfy_client_factory: Callable[[], NtfyClient] | None = None,
    ) -> None:
        self.scheduled_time = time(hour=hour, minute=minute)
        self.session_factory = session_factory
        self.ntfy_client_factory = ntfy_client_factory or (
            lambda: NtfyClient("http://ntfy:80")
        )
        self._task: asyncio.Task[Any] | None = None
        self._running = False

    def start(self) -> None:
        """Start the scheduler in the background."""
        if self._running:
            logger.warning("NotificationScheduler is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"NotificationScheduler started, scheduled for {self.scheduled_time} UTC daily"
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

        logger.info("NotificationScheduler stopped")

    def _next_run_time(self, now: datetime | None = None) -> datetime:
        """Calculate the next run time in UTC."""
        if now is None:
            now = datetime.now(UTC)

        next_run = datetime.combine(now.date(), self.scheduled_time, tzinfo=UTC)

        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run

    async def _run_loop(self) -> None:
        """Background loop that waits and executes notifications."""
        while self._running:
            next_run = self._next_run_time()
            sleep_seconds = (next_run - datetime.now(UTC)).total_seconds()

            if sleep_seconds > 0:
                logger.info(
                    f"Next notification check at {next_run} UTC (in {sleep_seconds:.1f} seconds)"
                )
                try:
                    await asyncio.sleep(sleep_seconds)
                except asyncio.CancelledError:
                    break

            if not self._running:
                break

            logger.info("Starting scheduled notification check")
            try:
                await self._execute()
                logger.info("Scheduled notification check completed successfully")
            except Exception:
                logger.exception("Scheduled notification check failed")

    async def _execute(self) -> None:
        """Perform one notification run."""
        with self.session_factory() as session:
            ntfy_client = self.ntfy_client_factory()
            usecase = provide(
                session=session,
                ntfy_client=ntfy_client,
                ntfy_public_url="",
            )
            results = await usecase.execute_all()
            notified = sum(1 for r in results if r.notification_sent)
            logger.info(
                "Notification run complete: %d users checked, %d notified",
                len(results),
                notified,
            )
