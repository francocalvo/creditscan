"""Currency conversion domain models."""

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


class BatchCurrencyConversionRequest(SQLModel):
    """Request model for converting multiple amounts."""

    conversions: list[CurrencyConversionRequest]


class BatchCurrencyConversionResponse(SQLModel):
    """Response model for batch currency conversion."""

    results: list[CurrencyConversionResponse]
