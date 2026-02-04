"""Currency conversion endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.currency.domain.errors import UnsupportedCurrencyError
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
    _current_user: CurrentUser,
) -> Any:
    """Convert a single amount between currencies."""
    try:
        usecase = provide_convert_currency()
        return usecase.execute(request)
    except UnsupportedCurrencyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/convert/batch", response_model=BatchCurrencyConversionResponse)
def convert_currency_batch(
    request: BatchCurrencyConversionRequest,
    _current_user: CurrentUser,
) -> Any:
    """Convert multiple amounts between currencies."""
    try:
        usecase = provide_convert_currency_batch()
        return usecase.execute(request)
    except UnsupportedCurrencyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
