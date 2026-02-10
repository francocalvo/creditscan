"""Tests for the configuration settings."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettingsValidation:
    """Test Settings class validation."""

    def test_valid_notification_hour(self):
        """Test valid notification hour values."""
        # Test with valid hour at lower bound
        settings = Settings(
            PROJECT_NAME="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="password",
            POSTGRES_DB="db",
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="password",
            NOTIFICATION_HOUR=0,
        )
        assert settings.NOTIFICATION_HOUR == 0

        # Test with valid hour at upper bound
        settings = Settings(
            PROJECT_NAME="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="password",
            POSTGRES_DB="db",
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="password",
            NOTIFICATION_HOUR=23,
        )
        assert settings.NOTIFICATION_HOUR == 23

        # Test with valid hour in middle
        settings = Settings(
            PROJECT_NAME="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="password",
            POSTGRES_DB="db",
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="password",
            NOTIFICATION_HOUR=12,
        )
        assert settings.NOTIFICATION_HOUR == 12

    def test_invalid_notification_hour_too_low(self):
        """Test invalid notification hour value (negative)."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                PROJECT_NAME="test",
                POSTGRES_SERVER="localhost",
                POSTGRES_USER="user",
                POSTGRES_PASSWORD="password",
                POSTGRES_DB="db",
                FIRST_SUPERUSER="admin@example.com",
                FIRST_SUPERUSER_PASSWORD="password",
                NOTIFICATION_HOUR=-1,
            )
        assert "NOTIFICATION_HOUR must be between 0 and 23" in str(exc_info.value)

    def test_invalid_notification_hour_too_high(self):
        """Test invalid notification hour value (> 23)."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                PROJECT_NAME="test",
                POSTGRES_SERVER="localhost",
                POSTGRES_USER="user",
                POSTGRES_PASSWORD="password",
                POSTGRES_DB="db",
                FIRST_SUPERUSER="admin@example.com",
                FIRST_SUPERUSER_PASSWORD="password",
                NOTIFICATION_HOUR=24,
            )
        assert "NOTIFICATION_HOUR must be between 0 and 23" in str(exc_info.value)

    def test_valid_notification_minute(self):
        """Test valid notification minute values."""
        # Test with valid minute at lower bound
        settings = Settings(
            PROJECT_NAME="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="password",
            POSTGRES_DB="db",
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="password",
            NOTIFICATION_MINUTE=0,
        )
        assert settings.NOTIFICATION_MINUTE == 0

        # Test with valid minute at upper bound
        settings = Settings(
            PROJECT_NAME="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="password",
            POSTGRES_DB="db",
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="password",
            NOTIFICATION_MINUTE=59,
        )
        assert settings.NOTIFICATION_MINUTE == 59

        # Test with valid minute in middle
        settings = Settings(
            PROJECT_NAME="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="password",
            POSTGRES_DB="db",
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="password",
            NOTIFICATION_MINUTE=30,
        )
        assert settings.NOTIFICATION_MINUTE == 30

    def test_invalid_notification_minute_too_low(self):
        """Test invalid notification minute value (negative)."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                PROJECT_NAME="test",
                POSTGRES_SERVER="localhost",
                POSTGRES_USER="user",
                POSTGRES_PASSWORD="password",
                POSTGRES_DB="db",
                FIRST_SUPERUSER="admin@example.com",
                FIRST_SUPERUSER_PASSWORD="password",
                NOTIFICATION_MINUTE=-1,
            )
        assert "NOTIFICATION_MINUTE must be between 0 and 59" in str(exc_info.value)

    def test_invalid_notification_minute_too_high(self):
        """Test invalid notification minute value (> 59)."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                PROJECT_NAME="test",
                POSTGRES_SERVER="localhost",
                POSTGRES_USER="user",
                POSTGRES_PASSWORD="password",
                POSTGRES_DB="db",
                FIRST_SUPERUSER="admin@example.com",
                FIRST_SUPERUSER_PASSWORD="password",
                NOTIFICATION_MINUTE=60,
            )
        assert "NOTIFICATION_MINUTE must be between 0 and 59" in str(exc_info.value)

    def test_default_notification_time(self):
        """Test default notification time values."""
        settings = Settings(
            PROJECT_NAME="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="password",
            POSTGRES_DB="db",
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="password",
        )
        assert settings.NOTIFICATION_HOUR == 22
        assert settings.NOTIFICATION_MINUTE == 0

    def test_notification_time_from_env(self, monkeypatch):
        """Test that notification time is read from environment variables."""
        monkeypatch.setenv("NOTIFICATION_HOUR", "15")
        monkeypatch.setenv("NOTIFICATION_MINUTE", "45")

        # Create settings with minimal required fields
        settings = Settings(
            PROJECT_NAME="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="password",
            POSTGRES_DB="db",
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="password",
        )

        assert settings.NOTIFICATION_HOUR == 15
        assert settings.NOTIFICATION_MINUTE == 45

    def test_notification_time_env_validation(self, monkeypatch):
        """Test that invalid env variables for notification time cause clear error."""
        monkeypatch.setenv("NOTIFICATION_HOUR", "25")

        with pytest.raises(ValidationError) as exc_info:
            Settings(
                PROJECT_NAME="test",
                POSTGRES_SERVER="localhost",
                POSTGRES_USER="user",
                POSTGRES_PASSWORD="password",
                POSTGRES_DB="db",
                FIRST_SUPERUSER="admin@example.com",
                FIRST_SUPERUSER_PASSWORD="password",
            )

        assert "NOTIFICATION_HOUR must be between 0 and 23" in str(exc_info.value)
