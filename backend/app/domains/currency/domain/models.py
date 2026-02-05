"""Currency conversion domain models."""

import uuid
from datetime import UTC, datetime
from datetime import date as Date
from decimal import Decimal

from pydantic import field_validator
from sqlmodel import Field, SQLModel  # type: ignore


class CurrencyConversionRequest(SQLModel):
    """Request model for converting an amount from one currency to another."""

    amount: Decimal
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3)
    date: Date | None = None

    @field_validator("from_currency", "to_currency")
    @classmethod
    def _normalize_currency_code(cls, value: str) -> str:
        """Normalize currency code to uppercase ISO-like 3-letter format."""
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("Currency code must be 3 alphabetic characters")
        return normalized


class CurrencyConversionResponse(SQLModel):
    """Response model for a currency conversion."""

    original_amount: Decimal
    converted_amount: Decimal
    from_currency: str
    to_currency: str
    rate: Decimal
    rate_date: Date


class BatchCurrencyConversionRequest(SQLModel):
    """Request model for converting multiple amounts."""

    conversions: list[CurrencyConversionRequest]


class BatchCurrencyConversionResponse(SQLModel):
    """Response model for batch currency conversion."""

    results: list[CurrencyConversionResponse]


class ExchangeRatePublic(SQLModel):
    """Public response model for an exchange rate."""

    rate_date: Date
    buy_rate: Decimal
    sell_rate: Decimal
    average_rate: Decimal
    source: str
    fetched_at: datetime


class ExchangeRatesResponse(SQLModel):
    """Response model for multiple exchange rates."""

    base_currency: str
    target_currency: str
    rates: list[ExchangeRatePublic]


# Exchange rate database model
class ExchangeRate(SQLModel, table=True):
    """Database model for storing exchange rates."""

    __tablename__ = "exchange_rate"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Rate data
    from_currency: str = Field(max_length=3, default="USD")
    to_currency: str = Field(max_length=3, default="ARS")
    buy_rate: Decimal = Field(decimal_places=4, max_digits=12)
    sell_rate: Decimal = Field(decimal_places=4, max_digits=12)

    # Metadata
    rate_date: Date = Field(index=True, unique=True)
    source: str = Field(max_length=50, default="cronista_mep")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))  # type: ignore[arg-type]

    @property
    def average_rate(self) -> Decimal:
        """Calculate the average of buy and sell rates."""
        return (self.buy_rate + self.sell_rate) / 2
