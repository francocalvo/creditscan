"""Usecase for converting a single currency amount."""

from sqlmodel import Session

from app.domains.currency.domain.models import (
    CurrencyConversionRequest,
    CurrencyConversionResponse,
)
from app.domains.currency.repository.exchange_rate_repository import (
    provide as provide_repository,
)
from app.domains.currency.service.currency_conversion_service import (
    CurrencyConversionService,
)


class ConvertCurrencyUseCase:
    """Usecase for converting a single amount from one currency to another."""

    def __init__(self, service: CurrencyConversionService) -> None:
        """Initialize the usecase with a conversion service.

        Args:
            service: Currency conversion service.
        """
        self.service = service

    def execute(
        self, request: CurrencyConversionRequest, session: Session
    ) -> CurrencyConversionResponse:
        """Execute the conversion.

        Args:
            request: Currency conversion request.
            session: Database session for rate lookup.

        Returns:
            CurrencyConversionResponse with converted amount, rate, and rate_date.
        """
        converted, rate, rate_date = self.service.convert_amount(
            session=session,
            amount=request.amount,
            from_currency=request.from_currency,
            to_currency=request.to_currency,
            target_date=request.date,
        )
        return CurrencyConversionResponse(
            original_amount=request.amount,
            converted_amount=converted,
            from_currency=request.from_currency,
            to_currency=request.to_currency,
            rate=rate,
            rate_date=rate_date,
        )


def provide(session: Session) -> ConvertCurrencyUseCase:
    """Provide an instance of ConvertCurrencyUseCase.

    Args:
        session: Database session.

    Returns:
        ConvertCurrencyUseCase instance.
    """
    repository = provide_repository(session)
    service = CurrencyConversionService(repository)
    return ConvertCurrencyUseCase(service)
