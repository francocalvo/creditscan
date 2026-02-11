"""Upload job domain models."""

import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy import Uuid as SAUuid
from sqlmodel import Field, SQLModel


class UploadJobStatus(str, Enum):
    """Status of an upload job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


# Database table model
class UploadJob(SQLModel, table=True):
    """Database model for upload jobs."""

    __tablename__ = "upload_job"

    # Unique constraint to prevent race-condition duplicates
    __table_args__ = (
        UniqueConstraint("user_id", "file_hash", name="uq_upload_job_user_file_hash"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    card_id: uuid.UUID = Field(foreign_key="credit_card.id", index=True)
    status: UploadJobStatus = Field(default=UploadJobStatus.PENDING, index=True)
    file_hash: str = Field(max_length=64, index=True)
    file_path: str = Field(max_length=500)
    file_size: int
    statement_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            SAUuid(),
            ForeignKey("card_statement.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    error_message: str | None = Field(default=None, max_length=2000)
    retry_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)


# For creating new records
class UploadJobCreate(SQLModel):
    """Model for creating upload job."""

    user_id: uuid.UUID
    card_id: uuid.UUID
    file_hash: str
    file_path: str
    file_size: int


# Public API response model
class UploadJobPublic(SQLModel):
    """Public model for upload jobs."""

    id: uuid.UUID
    status: UploadJobStatus
    statement_id: uuid.UUID | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime | None
    completed_at: datetime | None
