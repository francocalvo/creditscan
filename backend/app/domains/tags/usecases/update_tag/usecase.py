"""Usecase for updating a tag."""

import uuid

from sqlmodel import Session

from app.domains.tags.domain.models import TagPublic, TagUpdate
from app.domains.tags.service import TagService
from app.domains.tags.service import provide as provide_service


class UpdateTagUseCase:
    """Usecase for updating a tag."""

    def __init__(self, service: TagService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self,
        tag_id: uuid.UUID,
        tag_data: TagUpdate,
    ) -> TagPublic:
        """Execute the usecase to update a tag.

        Args:
            tag_id: The ID of the tag to update
            tag_data: The tag data to update

        Returns:
            TagPublic: The updated tag
        """
        return self.service.update_tag(tag_id, tag_data)


def provide(session: Session) -> UpdateTagUseCase:
    """Provide an instance of UpdateTagUseCase.

    Args:
        session: The database session to use.
    """
    return UpdateTagUseCase(provide_service(session))
