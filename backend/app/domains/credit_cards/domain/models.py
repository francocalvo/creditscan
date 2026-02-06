"""Credit card domain models."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DECIMAL, Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class CardBrand(str, Enum):
    """Enumeration for credit card brands."""

    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    OTHER = "other"


class LimitSource(str, Enum):
    """Enumeration for credit card limit sources."""

    MANUAL = "manual"
    STATEMENT = "statement"


# Base model with shared properties
class CreditCardBase(SQLModel):
    """Base model for credit cards."""

    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    bank: str = Field(max_length=100)
    brand: CardBrand
    last4: str = Field(max_length=4)
    alias: str | None = Field(default=None, max_length=100)
    default_currency: str = Field(default="ARS", max_length=3)


# For creating new records
class CreditCardCreate(CreditCardBase):
    """Model for creating credit card."""

    pass


# Database table model
class CreditCard(CreditCardBase, table=True):
    """Database model for credit cards."""

    __tablename__ = "credit_card"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, alias="card_id")
    credit_limit: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(precision=32, scale=2), nullable=True)
    )
    limit_last_updated_at: datetime | None = Field(default=None)
    limit_source: LimitSource | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(LimitSource, values_callable=lambda e: [m.value for m in e]),
            nullable=True,
        ),
    )


# Public API response model
class CreditCardPublic(CreditCardBase):
    """Public model for credit cards."""

    id: uuid.UUID
    credit_limit: Decimal | None = None
    limit_last_updated_at: datetime | None = None
    limit_source: LimitSource | None = None
    outstanding_balance: Decimal = Decimal("0")


# For updates (all fields optional)
class CreditCardUpdate(SQLModel):
    """Model for updating credit card."""

    bank: str | None = Field(default=None, max_length=100)
    brand: CardBrand | None = None
    last4: str | None = Field(default=None, max_length=4)
    alias: str | None = Field(default=None, max_length=100)
    default_currency: str | None = Field(default=None, max_length=3)
    credit_limit: Decimal | None = Field(default=None, gt=0)


# For paginated lists
class CreditCardsPublic(SQLModel):
    """Response model for paginated credit cards."""

    data: list[CreditCardPublic]
    count: int
