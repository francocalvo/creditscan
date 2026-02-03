"""Currency conversion service for multi-currency balance handling.

Exchanges:
    CurrencyService: High-level currency conversion orchestration
    provide: Provider function for dependency injection
"""

import logging
from decimal import Decimal

from app.pkgs.currency.client import ExchangeRateClient
from app.pkgs.extraction.models import Money

logger = logging.getLogger(__name__)


class CurrencyService:
    """Service for converting and summing multi-currency balances."""

    def __init__(self, client: ExchangeRateClient) -> None:
        """Initialize currency service.

        Args:
            client: Exchange rate API client
        """
        self.client = client

    async def convert_balance(
        self, balances: list[Money], target_currency: str
    ) -> Decimal:
        """Convert multiple currency balances to target currency and sum.

        Args:
            balances: List of Money objects with amounts and currencies
            target_currency: Target currency code (e.g., "USD")

        Returns:
            Total converted amount rounded to 2 decimal places

        Raises:
            httpx.HTTPStatusError: If API request fails
            KeyError: If currency not found in rates
            httpx.TimeoutException: If request times out
        """
        total = Decimal("0")

        for balance in balances:
            if balance.currency == target_currency:
                # Same currency: add directly
                total += balance.amount
                logger.info(
                    f"Added {balance.amount} {balance.currency} (same currency)"
                )
            else:
                # Different currency: fetch rate and convert
                rate = await self.client.get_rate(
                    from_currency=balance.currency, to_currency=target_currency
                )
                converted_amount = balance.amount * rate
                total += converted_amount
                logger.info(
                    f"Converted {balance.amount} {balance.currency} -> "
                    f"{converted_amount} {target_currency} "
                    f"(rate: {rate})"
                )

        # Round to 2 decimal places
        rounded_total = total.quantize(Decimal("0.01"))
        logger.info(f"Total converted balance: {rounded_total} {target_currency}")
        return rounded_total


def provide() -> CurrencyService:
    """Provider function for dependency injection.

    Returns:
        Configured CurrencyService instance
    """
    from app.core.config import settings

    client = ExchangeRateClient(api_key=settings.EXCHANGE_RATE_API_KEY)
    return CurrencyService(client)
