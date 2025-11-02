"""Usecase for deleting a tag."""

import uuid

from app.domains.tags.service import TagService
from app.domains.tags.service.tag_service import provide as provide_service


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


def provide() -> DeleteTagUseCase:
    """Provide an instance of DeleteTagUseCase."""
    return DeleteTagUseCase(provide_service())
