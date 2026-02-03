"""Tag domain models."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


# Base model with shared properties
class TagBase(SQLModel):
    """Base model for tags."""

    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    label: str = Field(max_length=200)


# For creating new records
class TagCreate(TagBase):
    """Model for creating tag."""

    pass


# Database table model
class Tag(TagBase, table=True):
    """Database model for tags."""

    __tablename__ = "tags"

    tag_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = Field(default=None)


# Public API response model
class TagPublic(TagBase):
    """Public model for tags."""

    tag_id: uuid.UUID
    created_at: datetime


# For updates (all fields optional)
class TagUpdate(SQLModel):
    """Model for updating tag."""

    label: str | None = Field(default=None, max_length=200)


# For paginated lists
class TagsPublic(SQLModel):
    """Response model for paginated tags."""

    data: list[TagPublic]
    count: int
    pagination: dict[str, int] | None = None
