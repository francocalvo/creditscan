"""Transaction tag domain models."""

import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Uuid as SAUuid
from sqlmodel import Field, SQLModel


# Database table model (junction table)
class TransactionTag(SQLModel, table=True):
    """Database model for transaction tags (junction table)."""

    __tablename__ = "transaction_tags"

    transaction_id: uuid.UUID = Field(
        sa_column=Column(
            SAUuid(),
            ForeignKey("transaction.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    tag_id: uuid.UUID = Field(
        sa_column=Column(
            SAUuid(),
            ForeignKey("tags.tag_id", ondelete="CASCADE"),
            primary_key=True,
        )
    )


# For creating new relationships
class TransactionTagCreate(SQLModel):
    """Model for creating a transaction tag relationship."""

    transaction_id: uuid.UUID
    tag_id: uuid.UUID


# Public API response model
class TransactionTagPublic(SQLModel):
    """Public model for transaction tags."""

    transaction_id: uuid.UUID
    tag_id: uuid.UUID
