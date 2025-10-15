"""Card statement domain models."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import DECIMAL, Column
from sqlmodel import Field, SQLModel


# Base model with shared properties
class CardStatementBase(SQLModel):
    """Base model for card statements."""

    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    card_last4: str = Field(max_length=4)
    card_brand: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    close_date: date | None = None
    due_date: date | None = None
    previous_balance: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(32, 2))
    )
    current_balance: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(32, 2))
    )
    minimum_payment: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(32, 2))
    )


# For creating new records
class CardStatementCreate(CardStatementBase):
    """Model for creating card statement."""

    pass


# Database table model
class CardStatement(CardStatementBase, table=True):
    """Database model for card statements."""

    __tablename__ = "card_statement"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, alias="statement_id"
    )


# Public API response model
class CardStatementPublic(CardStatementBase):
    """Public model for card statements."""

    id: uuid.UUID


# For updates (all fields optional)
class CardStatementUpdate(SQLModel):
    """Model for updating card statement."""

    card_last4: str | None = Field(default=None, max_length=4)
    card_brand: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    close_date: date | None = None
    due_date: date | None = None
    previous_balance: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(32, 2))
    )
    current_balance: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(32, 2))
    )
    minimum_payment: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(32, 2))
    )


# For paginated lists
class CardStatementsPublic(SQLModel):
    """Response model for paginated card statements."""

    data: list[CardStatementPublic]
    count: int
    pagination: dict[str, int] | None = None
