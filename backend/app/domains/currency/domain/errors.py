"""Currency domain errors."""

from datetime import date as Date


class CurrencyError(Exception):
    """Base exception for currency domain errors."""


class UnsupportedCurrencyError(CurrencyError):
    """Raised when a currency code is not supported by the converter."""

    def __init__(self, currency: str) -> None:
        super().__init__(f"Unsupported currency: {currency}")
        self.currency = currency


class RateNotFoundError(CurrencyError):
    """Raised when no exchange rate exists for a requested date."""

    def __init__(self, date: Date) -> None:
        super().__init__(f"No exchange rate available for {date}")
        self.date = date


class ExtractionError(CurrencyError):
    """Raised when rate extraction from external source fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
