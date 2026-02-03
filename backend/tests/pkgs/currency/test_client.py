"""Tests for ExchangeRateClient."""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from httpx import HTTPStatusError, TimeoutException

from app.pkgs.currency.client import ExchangeRateClient


class TestExchangeRateClient:
    """Tests for ExchangeRateClient class."""

    def test_init_creates_client_with_defaults(self) -> None:
        """Test that client initializes with default values."""
        client = ExchangeRateClient()
        assert client.api_key == ""
        assert client.base_url == "https://api.exchangerate-api.com/v4"

    def test_init_creates_client_with_custom_url(self) -> None:
        """Test that client initializes with custom base URL."""
        client = ExchangeRateClient(
            api_key="test-key", base_url="https://custom.api.com"
        )
        assert client.api_key == "test-key"
        assert client.base_url == "https://custom.api.com"

    def test_get_rate_fetches_from_api(self) -> None:
        """Test that get_rate fetches and returns the correct rate."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "rates": {
                "EUR": "0.85",
                "GBP": "0.75",
                "USD": "1.0",
            }
        }
        mock_response.raise_for_status = Mock()

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.get.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = ExchangeRateClient()
                rate = await client.get_rate("USD", "EUR")

                assert rate == Decimal("0.85")

        asyncio.run(run_test())

    def test_get_rate_handles_api_error(self) -> None:
        """Test that get_rate raises HTTPStatusError on API error."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_response = Mock()
                mock_response.status_code = 500
                mock_client.get.side_effect = HTTPStatusError(
                    "Internal Server Error",
                    request=Mock(),
                    response=mock_response,
                )
                mock_client_class.return_value = mock_client

                client = ExchangeRateClient()

                with pytest.raises(HTTPStatusError):
                    await client.get_rate("USD", "EUR")

        asyncio.run(run_test())

    def test_get_rate_handles_missing_currency(self) -> None:
        """Test that get_rate raises KeyError when currency not found."""
        mock_response = Mock()
        mock_response.json.return_value = {"rates": {"EUR": "0.85", "GBP": "0.75"}}
        mock_response.raise_for_status = Mock()

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.get.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = ExchangeRateClient()

                with pytest.raises(KeyError, match="Currency USD not found in rates"):
                    await client.get_rate("EUR", "USD")

        asyncio.run(run_test())

    def test_get_rate_converts_to_decimal(self) -> None:
        """Test that get_rate returns Decimal type (not float)."""
        mock_response = Mock()
        mock_response.json.return_value = {"rates": {"EUR": "0.8543"}}
        mock_response.raise_for_status = Mock()

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.get.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = ExchangeRateClient()
                rate = await client.get_rate("USD", "EUR")

                assert isinstance(rate, Decimal)
                assert rate == Decimal("0.8543")

        asyncio.run(run_test())

    def test_get_rate_handles_timeout(self) -> None:
        """Test that get_rate raises TimeoutException on timeout."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.get.side_effect = TimeoutException("Request timed out")
                mock_client_class.return_value = mock_client

                client = ExchangeRateClient()

                with pytest.raises(TimeoutException):
                    await client.get_rate("USD", "EUR")

        asyncio.run(run_test())
