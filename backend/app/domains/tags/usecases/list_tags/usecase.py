"""Usecase for listing tags."""

import uuid

from app.domains.tags.domain.models import TagsPublic
from app.domains.tags.service import TagService
from app.domains.tags.service.tag_service import provide as provide_service


class ListTagsUseCase:
    """Usecase for listing tags with pagination."""

    def __init__(self, service: TagService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: uuid.UUID | None = None,
    ) -> TagsPublic:
        """Execute the usecase to list tags.

        Args:
            skip: Number of records to skip
            limit: Number of records to return
            user_id: Optional filter by user ID

        Returns:
            TagsPublic: Paginated tags data
        """
        filters = {}
        if user_id:
            filters["user_id"] = user_id

        return self.service.list_tags(skip=skip, limit=limit, filters=filters)


def provide() -> ListTagsUseCase:
    """Provide an instance of ListTagsUseCase."""
    return ListTagsUseCase(provide_service())
