"""Currency conversion service.

This service provides currency conversion using database-backed exchange rates.
"""

from datetime import date as Date
from decimal import ROUND_HALF_UP, Decimal

from sqlmodel import Session

from app.domains.currency.domain.errors import RateNotFoundError
from app.domains.currency.domain.models import ExchangeRate
from app.domains.currency.repository.exchange_rate_repository import (
    ExchangeRateRepository,
)


class CurrencyConversionService:
    """Service for converting amounts between currencies using DB rates."""

    def __init__(self, repository: ExchangeRateRepository) -> None:
        """Initialize the conversion service with a rate repository.

        Args:
            repository: Exchange rate repository for accessing rate data.
        """
        self._repo = repository

    def is_supported(self, currency: str) -> bool:
        """Return True if currency is supported by the converter.

        Currently only USD and ARS are supported.
        """
        return currency in ("USD", "ARS")

    def _validate_currencies(self, from_currency: str, to_currency: str) -> None:
        """Validate that both currencies are supported.

        Args:
            from_currency: Source currency code.
            to_currency: Target currency code.

        Raises:
            UnsupportedCurrencyError: If either currency is not supported.
        """
        from app.domains.currency.domain.errors import UnsupportedCurrencyError

        if not self.is_supported(from_currency):
            raise UnsupportedCurrencyError(from_currency)
        if not self.is_supported(to_currency):
            raise UnsupportedCurrencyError(to_currency)

    def _get_exchange_rate(
        self, session: Session, target_date: Date | None = None
    ) -> ExchangeRate:
        """Get exchange rate for a target date with fallback logic.

        Args:
            session: Database session.
            target_date: Target date for the rate. If None, uses latest rate.

        Returns:
            ExchangeRate instance.

        Raises:
            RateNotFoundError: If no rate exists in the database.
        """
        # Try exact date match first if date is provided
        if target_date:
            rate = self._repo.get_rate_for_date(session, target_date)
            if rate:
                return rate

            # Fallback to closest date
            rate = self._repo.get_closest_rate(session, target_date)
            if rate:
                return rate
        else:
            # No date provided, use latest rate
            rate = self._repo.get_latest_rate(session)
            if rate:
                return rate

        # No rate found
        date_str = str(target_date) if target_date else "latest"
        raise RateNotFoundError(
            Date.fromisoformat(date_str) if target_date else Date.today()
        )

    def convert_amount(
        self,
        session: Session,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        target_date: Date | None = None,
    ) -> tuple[Decimal, Decimal, Date]:
        """Convert an amount between currencies.

        Args:
            session: Database session for rate lookup.
            amount: Amount in from_currency.
            from_currency: Source currency code (3 letters).
            to_currency: Target currency code (3 letters).
            target_date: Optional date for the exchange rate. If None, uses latest rate.

        Returns:
            Tuple of (converted_amount, rate, rate_date) where:
            - converted_amount is the result of the conversion
            - rate is the multiplier: converted_amount = amount * rate
            - rate_date is the date of the rate that was used

        Raises:
            UnsupportedCurrencyError: If either currency is not supported.
            RateNotFoundError: If no exchange rate is available.
        """
        self._validate_currencies(from_currency, to_currency)

        # Same currency: return identity with rate 1 and today's date
        if from_currency == to_currency:
            converted = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return converted, Decimal("1"), Date.today()

        # Get exchange rate from database
        exchange_rate = self._get_exchange_rate(session, target_date)
        average_rate = exchange_rate.average_rate

        # Calculate conversion
        # USD -> ARS: multiply by average rate
        # ARS -> USD: divide by average rate (rate = 1 / average_rate)
        if from_currency == "USD" and to_currency == "ARS":
            rate = average_rate
            converted = (amount * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        elif from_currency == "ARS" and to_currency == "USD":
            rate = Decimal("1") / average_rate
            converted = (amount * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            # Should not happen due to validation, but for completeness
            converted = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            rate = Decimal("1")

        return converted, rate, exchange_rate.rate_date


def provide(repository: ExchangeRateRepository) -> CurrencyConversionService:
    """Provide a CurrencyConversionService instance.

    Args:
        repository: Exchange rate repository for DI.

    Returns:
        CurrencyConversionService instance.
    """
    return CurrencyConversionService(repository)
