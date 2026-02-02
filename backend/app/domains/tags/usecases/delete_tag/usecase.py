"""Usecase for deleting a tag."""

import uuid

from sqlmodel import Session

from app.domains.tags.service import TagService
from app.domains.tags.service import provide as provide_service


class DeleteTagUseCase:
    """Usecase for deleting a tag."""

    def __init__(self, service: TagService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, tag_id: uuid.UUID) -> None:
        """Execute the usecase to delete a tag.

        Args:
            tag_id: The ID of the tag to delete
        """
        self.service.delete_tag(tag_id)


def provide(session: Session) -> DeleteTagUseCase:
    """Provide an instance of DeleteTagUseCase.

    Args:
        session: The database session to use.
    """
    return DeleteTagUseCase(provide_service(session))
