"""Exchange rate API client for currency conversion.

Exchanges:
    ExchangeRateClient: HTTP client for exchange rate API
"""

import logging
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


class ExchangeRateClient:
    """Client for fetching exchange rates from ExchangeRate-API."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.exchangerate-api.com/v4",
    ) -> None:
        """Initialize exchange rate client.

        Args:
            api_key: API key for ExchangeRate-API (optional for v4)
            base_url: Base URL for ExchangeRate-API
        """
        self.api_key = api_key
        self.base_url = base_url
        logger.info(f"ExchangeRateClient initialized: {base_url}")

    async def get_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Fetch exchange rate between two currencies.

        Args:
            from_currency: Source currency code (e.g., "USD")
            to_currency: Target currency code (e.g., "EUR")

        Returns:
            Exchange rate as Decimal

        Raises:
            httpx.HTTPStatusError: If API request fails
            KeyError: If currency not found in response
            httpx.TimeoutException: If request times out
        """
        url = f"{self.base_url}/latest/{from_currency}"
        logger.info(f"Fetching exchange rate: {from_currency} -> {to_currency}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                # Extract rate from response
                rates = data.get("rates", {})
                if to_currency not in rates:
                    raise KeyError(f"Currency {to_currency} not found in rates")

                rate = rates[to_currency]
                # Convert to Decimal using string to avoid float precision issues
                decimal_rate = Decimal(str(rate))
                logger.info(
                    f"Exchange rate {from_currency}->{to_currency}: {decimal_rate}"
                )
                return decimal_rate

            except httpx.HTTPStatusError as e:
                logger.error(f"API error fetching exchange rate: {e}")
                raise
            except httpx.TimeoutException as e:
                logger.error(f"Timeout fetching exchange rate: {e}")
                raise
            except KeyError as e:
                logger.error(f"Currency not found: {e}")
                raise
