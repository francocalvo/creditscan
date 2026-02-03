"""Currency conversion service for multi-currency balance handling.

Exchanges:
    CurrencyService: High-level currency conversion orchestration
    provide: Provider function for dependency injection
"""

import logging
from decimal import Decimal

import httpx

from app.domains.upload_jobs.domain.errors import CurrencyConversionError
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
            CurrencyConversionError: If conversion fails
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
                try:
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
                except httpx.HTTPStatusError as e:
                    logger.error(
                        f"API error converting {balance.currency} to {target_currency}: {e}"
                    )
                    raise CurrencyConversionError(
                        f"Failed to fetch exchange rate for {balance.currency}",
                        source_currency=balance.currency,
                    ) from e
                except httpx.TimeoutException as e:
                    logger.error(
                        f"Timeout converting {balance.currency} to {target_currency}"
                    )
                    raise CurrencyConversionError(
                        f"Timeout fetching exchange rate for {balance.currency}",
                        source_currency=balance.currency,
                    ) from e
                except KeyError as e:
                    logger.error(
                        f"Currency not found: {balance.currency} or {target_currency}"
                    )
                    raise CurrencyConversionError(
                        f"Currency rate not available for {balance.currency}",
                        source_currency=balance.currency,
                    ) from e
                except Exception as e:
                    logger.error(
                        f"Unexpected error converting {balance.currency} to {target_currency}: {e}"
                    )
                    raise CurrencyConversionError(
                        f"Currency conversion failed for {balance.currency}",
                        source_currency=balance.currency,
                    ) from e

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
