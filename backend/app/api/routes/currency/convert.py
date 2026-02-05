"""Currency conversion endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, SessionDep
from app.domains.currency.domain.errors import (
    RateNotFoundError,
    UnsupportedCurrencyError,
)
from app.domains.currency.domain.models import (
    BatchCurrencyConversionRequest,
    BatchCurrencyConversionResponse,
    CurrencyConversionRequest,
    CurrencyConversionResponse,
)
from app.domains.currency.usecases.convert_currency import (
    provide as provide_convert_currency,
)
from app.domains.currency.usecases.convert_currency_batch import (
    provide as provide_convert_currency_batch,
)

router = APIRouter()


@router.post("/convert", response_model=CurrencyConversionResponse)
def convert_currency(
    request: CurrencyConversionRequest,
    session: SessionDep,
    _current_user: CurrentUser,
    date: str | None = Query(
        default=None,
        description="Optional date override (YYYY-MM-DD). Overrides date in request body if provided.",
    ),
) -> Any:
    """Convert a single amount between currencies.

    Uses database-backed exchange rates with fallback to closest date.

    Raises:
        HTTPException(400): If the currency pair is not supported or date format is invalid.
        HTTPException(404): If no exchange rate is found for the requested date (or fallback).
    """
    # If query parameter date is provided, override request body date
    if date:
        from datetime import date as Date

        try:
            request.date = Date.fromisoformat(date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {date}. Use YYYY-MM-DD.",
            )

    try:
        usecase = provide_convert_currency(session)
        return usecase.execute(request, session)
    except UnsupportedCurrencyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/convert/batch", response_model=BatchCurrencyConversionResponse)
def convert_currency_batch(
    request: BatchCurrencyConversionRequest,
    session: SessionDep,
    _current_user: CurrentUser,
    date: str | None = Query(
        default=None,
        description="Optional date override (YYYY-MM-DD). Overrides date in request body if provided for all conversions.",
    ),
) -> Any:
    """Convert multiple amounts between currencies.

    Uses database-backed exchange rates with fallback to closest date.

    Raises:
        HTTPException(400): If any currency pair is not supported or date format is invalid.
        HTTPException(404): If no exchange rate is found for the requested date (or fallback).
    """
    # If query parameter date is provided, override request body date for all conversions
    if date:
        from datetime import date as Date

        try:
            target_date = Date.fromisoformat(date)
            for conversion in request.conversions:
                conversion.date = target_date
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {date}. Use YYYY-MM-DD.",
            )

    try:
        usecase = provide_convert_currency_batch(session)
        return usecase.execute(request, session)
    except UnsupportedCurrencyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
