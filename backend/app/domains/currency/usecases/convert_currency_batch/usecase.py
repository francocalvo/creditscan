"""Usecase for converting multiple currency amounts."""

from sqlmodel import Session

from app.domains.currency.domain.models import (
    BatchCurrencyConversionRequest,
    BatchCurrencyConversionResponse,
    CurrencyConversionResponse,
)
from app.domains.currency.repository.exchange_rate_repository import (
    provide as provide_repository,
)
from app.domains.currency.service.currency_conversion_service import (
    CurrencyConversionService,
)


class ConvertCurrencyBatchUseCase:
    """Usecase for converting multiple amounts from one currency to another."""

    def __init__(self, service: CurrencyConversionService) -> None:
        """Initialize the usecase with a conversion service.

        Args:
            service: Currency conversion service.
        """
        self.service = service

    def execute(
        self, request: BatchCurrencyConversionRequest, session: Session
    ) -> BatchCurrencyConversionResponse:
        """Execute the batch conversion.

        Args:
            request: Batch currency conversion request.
            session: Database session for rate lookup.

        Returns:
            BatchCurrencyConversionResponse with list of conversion results.
        """
        results: list[CurrencyConversionResponse] = []
        for conversion in request.conversions:
            converted, rate, rate_date = self.service.convert_amount(
                session=session,
                amount=conversion.amount,
                from_currency=conversion.from_currency,
                to_currency=conversion.to_currency,
                target_date=conversion.date,
            )
            results.append(
                CurrencyConversionResponse(
                    original_amount=conversion.amount,
                    converted_amount=converted,
                    from_currency=conversion.from_currency,
                    to_currency=conversion.to_currency,
                    rate=rate,
                    rate_date=rate_date,
                )
            )

        return BatchCurrencyConversionResponse(results=results)


def provide(session: Session) -> ConvertCurrencyBatchUseCase:
    """Provide an instance of ConvertCurrencyBatchUseCase.

    Args:
        session: Database session.

    Returns:
        ConvertCurrencyBatchUseCase instance.
    """
    repository = provide_repository(session)
    service = CurrencyConversionService(repository)
    return ConvertCurrencyBatchUseCase(service)
