"""Pydantic models for credit card statement extraction results."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class Money(BaseModel):
    """Monetary amount with currency."""

    amount: Decimal
    currency: str  # 3-letter ISO 4217 code


class InstallmentInfo(BaseModel):
    """Installment payment information."""

    current: int
    total: int


class ExtractedTransaction(BaseModel):
    """A single transaction extracted from the statement."""

    date: date
    merchant: str
    coupon: str | None = None
    amount: Money
    installment: InstallmentInfo | None = None


class ExtractedCycle(BaseModel):
    """Billing cycle period information."""

    start: date
    end: date
    due_date: date
    next_cycle_start: date | None = None


class ExtractedCard(BaseModel):
    """Credit card identification information."""

    last_four: str | None = None
    holder_name: str | None = None


class ExtractedStatement(BaseModel):
    """Complete extracted statement data."""

    statement_id: str
    card: ExtractedCard | None = None
    period: ExtractedCycle
    previous_balance: list[Money] = []
    current_balance: list[Money]
    minimum_payment: list[Money] = []
    credit_limit: Money | None = None
    transactions: list[ExtractedTransaction]


class ExtractionResult(BaseModel):
    """Result wrapper for extraction attempts."""

    success: bool
    data: ExtractedStatement | None = None
    partial_data: dict[str, object] | None = None
    error: str | None = None
    model_used: str
