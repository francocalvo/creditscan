"""Tests for CurrencyService."""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.pkgs.currency.client import ExchangeRateClient
from app.pkgs.currency.service import CurrencyService, provide
from app.pkgs.extraction.models import Money


class TestCurrencyService:
    """Tests for CurrencyService class."""

    def test_init_creates_service_with_client(self) -> None:
        """Test that service initializes with ExchangeRateClient."""
        mock_client = ExchangeRateClient()
        service = CurrencyService(client=mock_client)

        assert service.client is mock_client

    def test_convert_balance_same_currency_no_api_call(self) -> None:
        """Test that same currency balances don't trigger API calls."""
        mock_client = ExchangeRateClient()
        service = CurrencyService(client=mock_client)

        balances = [
            Money(amount=Decimal("100.50"), currency="USD"),
            Money(amount=Decimal("200.75"), currency="USD"),
        ]

        async def run_test():
            total = await service.convert_balance(balances, "USD")
            assert total == Decimal("301.25")

        asyncio.run(run_test())

    def test_convert_balance_different_currency_calls_api(self) -> None:
        """Test that different currency triggers API call."""
        mock_client = ExchangeRateClient()
        mock_client.get_rate = AsyncMock(return_value=Decimal("0.85"))

        service = CurrencyService(client=mock_client)

        balances = [Money(amount=Decimal("100"), currency="EUR")]

        async def run_test():
            total = await service.convert_balance(balances, "USD")

            mock_client.get_rate.assert_called_once_with(
                from_currency="EUR", to_currency="USD"
            )
            assert total == Decimal("85.00")

        asyncio.run(run_test())

    def test_convert_balance_applies_rate_correctly(self) -> None:
        """Test that rate is applied correctly."""
        mock_client = ExchangeRateClient()
        mock_client.get_rate = AsyncMock(return_value=Decimal("0.85"))

        service = CurrencyService(client=mock_client)

        balances = [Money(amount=Decimal("100"), currency="EUR")]

        async def run_test():
            total = await service.convert_balance(balances, "USD")
            assert total == Decimal("85.00")  # 100 * 0.85

        asyncio.run(run_test())

    def test_convert_balance_sums_multiple_balances(self) -> None:
        """Test that multiple balances are summed correctly."""
        mock_client = ExchangeRateClient()
        mock_client.get_rate = AsyncMock(return_value=Decimal("1.2"))

        service = CurrencyService(client=mock_client)

        balances = [
            Money(amount=Decimal("100"), currency="EUR"),
            Money(amount=Decimal("200"), currency="EUR"),
            Money(amount=Decimal("150"), currency="EUR"),
        ]

        async def run_test():
            total = await service.convert_balance(balances, "USD")
            # (100 + 200 + 150) * 1.2 = 540
            assert total == Decimal("540.00")

        asyncio.run(run_test())

    def test_convert_balance_rounds_to_two_decimals(self) -> None:
        """Test that result is rounded to 2 decimal places."""
        mock_client = ExchangeRateClient()
        # Use a rate that produces more than 2 decimal places
        mock_client.get_rate = AsyncMock(return_value=Decimal("0.854321"))

        service = CurrencyService(client=mock_client)

        balances = [Money(amount=Decimal("100"), currency="EUR")]

        async def run_test():
            total = await service.convert_balance(balances, "USD")
            # 100 * 0.854321 = 85.4321 -> should round to 85.43
            assert total == Decimal("85.43")

        asyncio.run(run_test())

    def test_convert_balance_handles_empty_list(self) -> None:
        """Test that empty list returns 0.00."""
        mock_client = ExchangeRateClient()
        service = CurrencyService(client=mock_client)

        balances: list[Money] = []

        async def run_test():
            total = await service.convert_balance(balances, "USD")
            assert total == Decimal("0.00")

        asyncio.run(run_test())

    def test_convert_balance_mixed_currencies(self) -> None:
        """Test that mixed currencies are handled correctly."""
        mock_client = ExchangeRateClient()
        mock_client.get_rate = AsyncMock(
            side_effect=[
                Decimal("0.85"),  # EUR -> USD
                Decimal("1.25"),  # GBP -> USD
            ]
        )

        service = CurrencyService(client=mock_client)

        balances = [
            Money(amount=Decimal("100"), currency="USD"),  # Same
            Money(amount=Decimal("50"), currency="EUR"),  # Convert
            Money(amount=Decimal("30"), currency="GBP"),  # Convert
        ]

        async def run_test():
            total = await service.convert_balance(balances, "USD")
            # 100 + (50 * 0.85) + (30 * 1.25) = 100 + 42.5 + 37.5 = 180
            assert total == Decimal("180.00")

        asyncio.run(run_test())


class TestProvide:
    """Tests for the provide() function."""

    def test_provide_returns_configured_service(self) -> None:
        """Test that provide() returns configured CurrencyService."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.EXCHANGE_RATE_API_KEY = "test-key"

            service = provide()

            assert isinstance(service, CurrencyService)
            assert isinstance(service.client, ExchangeRateClient)
            assert service.client.api_key == "test-key"
