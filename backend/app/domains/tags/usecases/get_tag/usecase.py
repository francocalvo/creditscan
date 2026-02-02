"""Usecase for getting a tag by ID."""

import uuid

from sqlmodel import Session

from app.domains.tags.domain.models import TagPublic
from app.domains.tags.service import TagService
from app.domains.tags.service import provide as provide_service


class GetTagUseCase:
    """Usecase for getting a tag by ID."""

    def __init__(self, service: TagService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, tag_id: uuid.UUID) -> TagPublic:
        """Execute the usecase to get a tag.

        Args:
            tag_id: The ID of the tag to retrieve

        Returns:
            TagPublic: The tag data
        """
        return self.service.get_tag(tag_id)


def provide(session: Session) -> GetTagUseCase:
    """Provide an instance of GetTagUseCase.

    Args:
        session: The database session to use.
    """
    return GetTagUseCase(provide_service(session))
