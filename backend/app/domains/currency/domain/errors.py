"""Currency domain errors."""


class CurrencyError(Exception):
    """Base exception for currency domain errors."""


class UnsupportedCurrencyError(CurrencyError):
    """Raised when a currency code is not supported by the converter."""

    def __init__(self, currency: str) -> None:
        super().__init__(f"Unsupported currency: {currency}")
        self.currency = currency
