"""Tag service implementation."""

import uuid
from typing import Any

from sqlmodel import Session

from app.domains.tags.domain.models import (
    TagCreate,
    TagPublic,
    TagsPublic,
    TagUpdate,
)
from app.domains.tags.repository import TagRepository
from app.domains.tags.repository import provide as provide_repository


class TagService:
    """Service for tags."""

    def __init__(self, repository: TagRepository):
        """Initialize the service with a repository."""
        self.repository = repository

    def create_tag(self, tag_data: TagCreate) -> TagPublic:
        """Create a new tag."""
        tag = self.repository.create(tag_data)
        return TagPublic.model_validate(tag)

    def get_tag(self, tag_id: uuid.UUID) -> TagPublic:
        """Get a tag by ID."""
        tag = self.repository.get_by_id(tag_id)
        return TagPublic.model_validate(tag)

    def list_tags(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> TagsPublic:
        """List tags with pagination and filtering."""
        tags = self.repository.list(skip=skip, limit=limit, filters=filters)
        count = self.repository.count(filters=filters)

        return TagsPublic(
            data=[TagPublic.model_validate(t) for t in tags],
            count=count,
        )

    def update_tag(self, tag_id: uuid.UUID, tag_data: TagUpdate) -> TagPublic:
        """Update a tag."""
        tag = self.repository.update(tag_id, tag_data)
        return TagPublic.model_validate(tag)

    def delete_tag(self, tag_id: uuid.UUID) -> None:
        """Delete a tag."""
        self.repository.delete(tag_id)


def provide(session: Session) -> TagService:
    """Provide an instance of TagService.

    Args:
        session: The database session to use.
    """
    return TagService(provide_repository(session))
