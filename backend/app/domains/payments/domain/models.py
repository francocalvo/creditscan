"""Payment domain models."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import DECIMAL, Column, ForeignKey
from sqlalchemy import Uuid as SAUuid
from sqlmodel import Field, SQLModel


# Base model with shared properties
class PaymentBase(SQLModel):
    """Base model for payments."""

    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    statement_id: uuid.UUID = Field(foreign_key="card_statement.id", index=True)
    amount: Decimal = Field(sa_column=Column(DECIMAL(32, 2)))
    payment_date: date
    currency: str = Field(max_length=3)


# For creating new records
class PaymentCreate(PaymentBase):
    """Model for creating payment."""

    pass


# Database table model
class Payment(PaymentBase, table=True):
    """Database model for payments."""

    __tablename__ = "payment"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, alias="payment_id"
    )
    statement_id: uuid.UUID = Field(
        sa_column=Column(
            SAUuid(),
            ForeignKey("card_statement.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )


# Public API response model
class PaymentPublic(PaymentBase):
    """Public model for payments."""

    id: uuid.UUID


# For updates (all fields optional)
class PaymentUpdate(SQLModel):
    """Model for updating payment."""

    statement_id: uuid.UUID | None = None
    amount: Decimal | None = Field(default=None, sa_column=Column(DECIMAL(32, 2)))
    payment_date: date | None = None
    currency: str | None = Field(default=None, max_length=3)


# For paginated lists
class PaymentsPublic(SQLModel):
    """Response model for paginated payments."""

    data: list[PaymentPublic]
    count: int
    pagination: dict[str, int] | None = None
