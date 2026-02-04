"""Usecase for converting a single currency amount."""

from app.domains.currency.domain.models import (
    CurrencyConversionRequest,
    CurrencyConversionResponse,
)
from app.domains.currency.service import CurrencyConversionService
from app.domains.currency.service import provide as provide_service


class ConvertCurrencyUseCase:
    """Usecase for converting a single amount from one currency to another."""

    def __init__(self, service: CurrencyConversionService) -> None:
        """Initialize the usecase with a conversion service."""
        self.service = service

    def execute(self, request: CurrencyConversionRequest) -> CurrencyConversionResponse:
        """Execute the conversion.

        Args:
            request: Currency conversion request.

        Returns:
            CurrencyConversionResponse with converted amount and rate.
        """
        converted, rate = self.service.convert_amount(
            amount=request.amount,
            from_currency=request.from_currency,
            to_currency=request.to_currency,
        )
        return CurrencyConversionResponse(
            original_amount=request.amount,
            converted_amount=converted,
            from_currency=request.from_currency,
            to_currency=request.to_currency,
            rate=rate,
        )


def provide() -> ConvertCurrencyUseCase:
    """Provide an instance of ConvertCurrencyUseCase."""
    return ConvertCurrencyUseCase(provide_service())
