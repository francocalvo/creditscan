"""Transaction domain models."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import DECIMAL, Column
from sqlmodel import Field, SQLModel  # type: ignore


# Base model with shared properties
class TransactionBase(SQLModel):
    """Base model for transactions."""

    statement_id: uuid.UUID = Field(foreign_key="card_statement.id", index=True)
    txn_date: date
    payee: str = Field(max_length=200)
    description: str = Field(max_length=500)
    amount: Decimal = Field(sa_column=Column(DECIMAL(32, 2)))
    currency: str = Field(max_length=3)
    coupon: str | None = Field(default=None, max_length=200)
    installment_cur: int | None = None
    installment_tot: int | None = None


# For creating new records
class TransactionCreate(TransactionBase):
    """Model for creating transaction."""

    pass


# Database table model
class Transaction(TransactionBase, table=True):
    """Database model for transactions."""

    __tablename__ = "transaction"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, alias="transaction_id"
    )


# Public API response model
class TransactionPublic(TransactionBase):
    """Public model for transactions."""

    id: uuid.UUID


# For updates (all fields optional)
class TransactionUpdate(SQLModel):
    """Model for updating transaction."""

    txn_date: date | None = None
    payee: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    amount: Decimal | None = Field(default=None, sa_column=Column(DECIMAL(32, 2)))
    currency: str | None = Field(default=None, max_length=3)
    coupon: str | None = Field(default=None, max_length=200)
    installment_cur: int | None = None
    installment_tot: int | None = None


# For paginated lists
class TransactionsPublic(SQLModel):
    """Response model for paginated transactions."""

    data: list[TransactionPublic]
    count: int
    pagination: dict[str, int] | None = None
