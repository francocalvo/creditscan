"""Unit tests for ExchangeRate model."""

import uuid
from datetime import UTC, date, datetime

from app.models import ExchangeRate


class TestExchangeRateModel:
    """Test ExchangeRate model schema and behavior."""

    def test_model_has_required_fields(self) -> None:
        """Test that all required fields exist with correct types."""
        rate = ExchangeRate(
            buy_rate=1458.74,
            sell_rate=1459.32,
            rate_date=date(2026, 2, 4),
        )

        assert isinstance(rate.id, uuid.UUID)
        assert rate.from_currency == "USD"
        assert rate.to_currency == "ARS"
        assert rate.buy_rate == 1458.74
        assert rate.sell_rate == 1459.32
        assert rate.rate_date == date(2026, 2, 4)
        assert rate.source == "cronista_mep"
        assert isinstance(rate.fetched_at, datetime)

    def test_field_defaults(self) -> None:
        """Test that default values are applied correctly."""
        rate = ExchangeRate(
            buy_rate=1458.74,
            sell_rate=1459.32,
            rate_date=date(2026, 2, 4),
        )

        assert rate.from_currency == "USD"
        assert rate.to_currency == "ARS"
        assert rate.source == "cronista_mep"

    def test_fetched_at_defaults_to_utc(self) -> None:
        """Test that fetched_at defaults to UTC timezone."""
        rate = ExchangeRate(
            buy_rate=1458.74,
            sell_rate=1459.32,
            rate_date=date(2026, 2, 4),
        )

        assert rate.fetched_at.tzinfo is not None
        assert rate.fetched_at.tzinfo == UTC

    def test_average_rate_property(self) -> None:
        """Test that average_rate property calculates correctly."""
        rate = ExchangeRate(
            buy_rate=1458.74,
            sell_rate=1459.32,
            rate_date=date(2026, 2, 4),
        )

        expected_average = (1458.74 + 1459.32) / 2
        assert rate.average_rate == expected_average
        assert rate.average_rate == 1459.03

    def test_average_rate_rounding(self) -> None:
        """Test that average_rate handles decimal precision correctly."""
        rate = ExchangeRate(
            buy_rate=1458.745,
            sell_rate=1459.325,
            rate_date=date(2026, 2, 4),
        )

        expected = (1458.745 + 1459.325) / 2
        assert rate.average_rate == expected
