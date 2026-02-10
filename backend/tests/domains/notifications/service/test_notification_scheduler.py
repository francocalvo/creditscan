"""Tests for notification scheduler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.notifications.service.notification_scheduler import (
    NotificationScheduler,
)


class TestNotificationScheduler:
    def test_next_run_time_same_day(self) -> None:
        scheduler = NotificationScheduler(hour=22, minute=0)
        now = datetime(2026, 2, 8, 15, 0, 0, tzinfo=UTC)

        next_run = scheduler._next_run_time(now)

        assert next_run == datetime(2026, 2, 8, 22, 0, 0, tzinfo=UTC)

    def test_next_run_time_next_day(self) -> None:
        scheduler = NotificationScheduler(hour=22, minute=0)
        now = datetime(2026, 2, 8, 23, 0, 0, tzinfo=UTC)

        next_run = scheduler._next_run_time(now)

        assert next_run == datetime(2026, 2, 9, 22, 0, 0, tzinfo=UTC)

    def test_next_run_time_exact_match(self) -> None:
        scheduler = NotificationScheduler(hour=22, minute=0)
        now = datetime(2026, 2, 8, 22, 0, 0, tzinfo=UTC)

        next_run = scheduler._next_run_time(now)

        assert next_run == datetime(2026, 2, 9, 22, 0, 0, tzinfo=UTC)

    @pytest.mark.asyncio
    async def test_execute_calls_use_case(self) -> None:
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        mock_ntfy_client = MagicMock()
        mock_ntfy_factory = MagicMock(return_value=mock_ntfy_client)

        scheduler = NotificationScheduler(
            session_factory=mock_session_factory,
            ntfy_client_factory=mock_ntfy_factory,
        )

        with patch(
            "app.domains.notifications.service.notification_scheduler.provide"
        ) as mock_provide:
            mock_usecase = MagicMock()
            mock_usecase.execute_all = AsyncMock(return_value=[])
            mock_provide.return_value = mock_usecase

            await scheduler._execute()

        mock_session_factory.assert_called_once()
        mock_ntfy_factory.assert_called_once()
        mock_provide.assert_called_once_with(
            session=mock_session,
            ntfy_client=mock_ntfy_client,
            ntfy_public_url="",
        )
        mock_usecase.execute_all.assert_called_once()
        mock_session.close.assert_called_once()
