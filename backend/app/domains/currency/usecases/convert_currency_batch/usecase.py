"""Usecase for converting multiple currency amounts."""

from app.domains.currency.domain.models import (
    BatchCurrencyConversionRequest,
    BatchCurrencyConversionResponse,
    CurrencyConversionResponse,
)
from app.domains.currency.service import CurrencyConversionService
from app.domains.currency.service import provide as provide_service


class ConvertCurrencyBatchUseCase:
    """Usecase for converting multiple amounts from one currency to another."""

    def __init__(self, service: CurrencyConversionService) -> None:
        """Initialize the usecase with a conversion service."""
        self.service = service

    def execute(
        self, request: BatchCurrencyConversionRequest
    ) -> BatchCurrencyConversionResponse:
        """Execute the batch conversion."""
        results: list[CurrencyConversionResponse] = []
        for conversion in request.conversions:
            converted, rate = self.service.convert_amount(
                amount=conversion.amount,
                from_currency=conversion.from_currency,
                to_currency=conversion.to_currency,
            )
            results.append(
                CurrencyConversionResponse(
                    original_amount=conversion.amount,
                    converted_amount=converted,
                    from_currency=conversion.from_currency,
                    to_currency=conversion.to_currency,
                    rate=rate,
                )
            )

        return BatchCurrencyConversionResponse(results=results)


def provide() -> ConvertCurrencyBatchUseCase:
    """Provide an instance of ConvertCurrencyBatchUseCase."""
    return ConvertCurrencyBatchUseCase(provide_service())
