"""Usecase for creating a tag."""

from sqlmodel import Session

from app.domains.tags.domain.models import TagCreate, TagPublic
from app.domains.tags.service import TagService
from app.domains.tags.service import provide as provide_service


class CreateTagUseCase:
    """Usecase for creating a tag."""

    def __init__(self, service: TagService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, tag_data: TagCreate) -> TagPublic:
        """Execute the usecase to create a tag.

        Args:
            tag_data: The tag data to create

        Returns:
            TagPublic: The created tag
        """
        return self.service.create_tag(tag_data)


def provide(session: Session) -> CreateTagUseCase:
    """Provide an instance of CreateTagUseCase.

    Args:
        session: The database session to use.
    """
    return CreateTagUseCase(provide_service(session))
