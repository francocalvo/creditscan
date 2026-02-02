"""Usecase for deleting a user."""

import uuid

from sqlmodel import Session

from app.domains.users.domain.errors import InvalidUserDataError
from app.domains.users.service import UserService
from app.domains.users.service import provide as provide_user_service


class DeleteUserUseCase:
    """Usecase for deleting a user."""

    def __init__(self, user_service: UserService) -> None:
        """Initialize the usecase with a user service.

        Args:
            user_service: Service for handling user operations
        """
        self.user_service = user_service

    def execute(
        self, user_id: uuid.UUID, current_user_id: uuid.UUID | None = None
    ) -> None:
        """Execute the usecase to delete a user.

        Args:
            user_id: The user ID to delete
            current_user_id: The current user ID (for validation)

        Raises:
            UserNotFoundError: If user is not found
            InvalidUserDataError: If trying to delete self as superuser
        """
        # Get the user to check if it exists and get properties
        user = self.user_service.user_repository.get_by_id(user_id)

        # Prevent superusers from deleting themselves
        if current_user_id and user_id == current_user_id and user.is_superuser:
            raise InvalidUserDataError(
                "Super users are not allowed to delete themselves"
            )

        # Delete the user
        self.user_service.delete_user(user_id)


def provide(session: Session) -> DeleteUserUseCase:
    """Provide an instance of DeleteUserUseCase.

    Args:
        session: The database session to use.

    Returns:
        DeleteUserUseCase: A new instance with the user service
    """
    return DeleteUserUseCase(provide_user_service(session))
