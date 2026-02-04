"""Currency conversion service.

This service provides deterministic, static exchange rates for the analytics MVP.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.domains.currency.domain.errors import UnsupportedCurrencyError


class CurrencyConversionService:
    """Service for converting amounts between a supported set of currencies."""

    _per_usd_rates: dict[str, Decimal] = {
        # 1 USD == X units of currency
        "USD": Decimal("1"),
        "ARS": Decimal("1000"),
        "EUR": Decimal("0.90"),
        "GBP": Decimal("0.80"),
    }

    def is_supported(self, currency: str) -> bool:
        """Return True if currency is supported by the converter."""
        return currency in self._per_usd_rates

    def convert_amount(
        self, amount: Decimal, from_currency: str, to_currency: str
    ) -> tuple[Decimal, Decimal]:
        """Convert an amount between currencies.

        Args:
            amount: Amount in from_currency.
            from_currency: Source currency code (3 letters).
            to_currency: Target currency code (3 letters).

        Returns:
            Tuple of (converted_amount, rate) where rate is the multiplier:
            converted_amount = amount * rate.
        """
        if not self.is_supported(from_currency):
            raise UnsupportedCurrencyError(from_currency)
        if not self.is_supported(to_currency):
            raise UnsupportedCurrencyError(to_currency)

        if from_currency == to_currency:
            return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), Decimal(
                "1"
            )

        rate = self._per_usd_rates[to_currency] / self._per_usd_rates[from_currency]
        converted = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return converted, rate


def provide() -> CurrencyConversionService:
    """Provide a CurrencyConversionService instance."""
    return CurrencyConversionService()
