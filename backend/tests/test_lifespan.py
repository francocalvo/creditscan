"""Tests for app lifecycle integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.asyncio
async def test_lifespan_scheduler_start_stop() -> None:
    """Test that RateExtractionScheduler starts and stops with app lifespan."""
    # We use a context manager patch to capture the instance created inside lifespan
    with patch("app.main.RateExtractionScheduler") as mock_scheduler_class:
        mock_scheduler_instance = mock_scheduler_class.return_value
        mock_scheduler_instance.start = MagicMock()
        mock_scheduler_instance.stop = AsyncMock()

        # Also mock resume_pending_jobs
        with patch("app.main.resume_pending_jobs", AsyncMock()) as mock_resume:
            # TestClient context manager triggers lifespan events
            with TestClient(app):
                # Verify startup
                mock_resume.assert_awaited_once()
                mock_scheduler_class.assert_called_once()
                mock_scheduler_instance.start.assert_called_once()

            # Verify shutdown (after exiting context manager)
            mock_scheduler_instance.stop.assert_awaited_once()
