"""Currency exchange rates query endpoints."""

from datetime import date as Date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, SessionDep
from app.domains.currency.domain.models import (
    ExchangeRate,
    ExchangeRatePublic,
    ExchangeRatesResponse,
)
from app.domains.currency.repository.exchange_rate_repository import (
    provide as provide_exchange_rate_repository,
)

router = APIRouter()

SUPPORTED_CURRENCIES = {"USD", "ARS"}


@router.get("/rates", response_model=ExchangeRatesResponse)
def get_exchange_rates(
    session: SessionDep,
    _current_user: CurrentUser,
    base: str = Query(default="USD", description="Base currency (e.g., USD)"),
    target: str = Query(default="ARS", description="Target currency (e.g., ARS)"),
    date: Date | None = Query(default=None, description="Query for a specific date"),
    start_date: Date | None = Query(
        default=None, description="Start date for range query"
    ),
    end_date: Date | None = Query(default=None, description="End date for range query"),
) -> Any:
    """Query exchange rates in three modes:

    - Latest: Default if no date params provided.
    - Single date: If 'date' is provided (with closest-date fallback).
    - Date range: If 'start_date' and 'end_date' are provided.

    Raises:
        HTTPException(400): If currency params are invalid, unsupported, or if date params are conflicting/invalid.
    """
    base = base.upper()
    target = target.upper()

    # Validation
    if base not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {base}")
    if target not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {target}")
    if base == target:
        raise HTTPException(
            status_code=400, detail="Base and target currencies cannot be the same"
        )

    if date and (start_date or end_date):
        raise HTTPException(
            status_code=400,
            detail="Cannot combine 'date' with 'start_date' or 'end_date'",
        )

    if (start_date and not end_date) or (end_date and not start_date):
        raise HTTPException(
            status_code=400,
            detail="Both 'start_date' and 'end_date' must be provided for a range query",
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="'start_date' must be less than or equal to 'end_date'",
        )

    repo = provide_exchange_rate_repository(session)
    rates_to_map: list[ExchangeRate] = []

    if date:
        rate = repo.get_rate_for_date(session, date)
        if not rate:
            rate = repo.get_closest_rate(session, date)
        if rate:
            rates_to_map = [rate]
    elif start_date and end_date:
        rates_to_map = repo.get_rates_in_range(session, start_date, end_date)
    else:
        # Latest
        rate = repo.get_latest_rate(session)
        if rate:
            rates_to_map = [rate]

    # Map to public response model with potential inversion
    is_inverted = base == "ARS" and target == "USD"
    public_rates: list[ExchangeRatePublic] = []

    for rate in rates_to_map:
        if is_inverted:
            # For ARS->USD, we invert rates to preserve the spread correctly
            # Inverted Buy Rate = 1 / Stored Sell Rate
            # Inverted Sell Rate = 1 / Stored Buy Rate
            buy_rate = Decimal(1) / rate.sell_rate
            sell_rate = Decimal(1) / rate.buy_rate
            average_rate = (buy_rate + sell_rate) / 2
        else:
            buy_rate = rate.buy_rate
            sell_rate = rate.sell_rate
            average_rate = (buy_rate + sell_rate) / 2

        public_rates.append(
            ExchangeRatePublic(
                rate_date=rate.rate_date,
                buy_rate=buy_rate.quantize(Decimal("0.0001")),
                sell_rate=sell_rate.quantize(Decimal("0.0001")),
                average_rate=average_rate.quantize(Decimal("0.0001")),
                source=rate.source,
                fetched_at=rate.fetched_at,
            )
        )

    return ExchangeRatesResponse(
        base_currency=base,
        target_currency=target,
        rates=public_rates,
    )
