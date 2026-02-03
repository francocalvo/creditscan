"""Tag repository implementation."""

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, func, select

from app.domains.tags.domain.errors import TagNotFoundError
from app.domains.tags.domain.models import Tag, TagCreate, TagUpdate


class TagRepository:
    """Repository for tags."""

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db_session = db_session

    def create(self, tag_data: TagCreate) -> Tag:
        """Create a new tag."""
        tag = Tag.model_validate(tag_data)
        self.db_session.add(tag)
        self.db_session.commit()
        self.db_session.refresh(tag)
        return tag

    def get_by_id(self, tag_id: uuid.UUID, include_deleted: bool = False) -> Tag:
        """Get a tag by ID.

        Args:
            tag_id: The ID of the tag to retrieve.
            include_deleted: If True, include soft-deleted tags. Defaults to False.

        Returns:
            The tag with the specified ID.

        Raises:
            TagNotFoundError: If the tag is not found or if it's deleted and include_deleted is False.
        """
        tag = self.db_session.get(Tag, tag_id)
        if not tag:
            raise TagNotFoundError(f"Tag with ID {tag_id} not found")
        if tag.deleted_at is not None and not include_deleted:
            raise TagNotFoundError(f"Tag with ID {tag_id} not found")
        return tag

    def list(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[Tag]:
        """List tags with pagination and filtering."""
        query = select(Tag).where(Tag.deleted_at.is_(None))

        if filters:
            for field, value in filters.items():
                if hasattr(Tag, field):
                    query = query.where(getattr(Tag, field) == value)

        result = self.db_session.exec(query.offset(skip).limit(limit))
        return list(result)

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count tags with optional filtering."""
        query = select(Tag).where(Tag.deleted_at.is_(None))

        if filters:
            for field, value in filters.items():
                if hasattr(Tag, field):
                    query = query.where(getattr(Tag, field) == value)

        count_q = (
            query.with_only_columns(func.count())
            .order_by(None)
            .select_from(query.get_final_froms()[0])
        )

        result = self.db_session.exec(count_q)
        for count in result:
            return count  # type: ignore
        return 0

    def update(self, tag_id: uuid.UUID, tag_data: TagUpdate) -> Tag:
        """Update a tag."""
        tag = self.get_by_id(tag_id)

        update_dict = tag_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(tag, field, value)

        self.db_session.add(tag)
        self.db_session.commit()
        self.db_session.refresh(tag)
        return tag

    def delete(self, tag_id: uuid.UUID) -> None:
        """Soft delete a tag by setting deleted_at timestamp."""
        tag = self.get_by_id(tag_id)
        tag.deleted_at = datetime.utcnow()
        self.db_session.add(tag)
        self.db_session.commit()


def provide(session: Session) -> TagRepository:
    """Provide an instance of TagRepository.

    Args:
        session: The database session to use.

    Returns:
        TagRepository: An instance of TagRepository with the given session.
    """
    return TagRepository(session)
