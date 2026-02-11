"""Usecase for updating a user."""

import uuid

from sqlmodel import Session

from app.domains.users.domain.errors import DuplicateUserError
from app.domains.users.domain.models import UserPublic, UserUpdate, UserUpdateMe
from app.domains.users.service import UserService
from app.domains.users.service import provide as provide_user_service


class UpdateUserUseCase:
    """Usecase for updating a user."""

    def __init__(self, user_service: UserService) -> None:
        """Initialize the usecase with a user service.

        Args:
            user_service: Service for handling user operations
        """
        self.user_service = user_service

    def execute(
        self, user_id: uuid.UUID, user_data: UserUpdate | UserUpdateMe
    ) -> UserPublic:
        """Execute the usecase to update a user.

        Args:
            user_id: The user ID to update
            user_data: User update data

        Returns:
            UserPublic: The updated user

        Raises:
            UserNotFoundError: If user is not found
            DuplicateUserError: If email is already taken by another user
        """
        # Check if user exists
        self.user_service.get_user(user_id)

        # Check if email is being updated and if it's already taken
        if hasattr(user_data, "email") and user_data.email:
            existing_user = self.user_service.get_user_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise DuplicateUserError("User with this email already exists")

        # Auto-generate ntfy_topic when enabling notifications without one
        if isinstance(user_data, UserUpdateMe):
            update_dict = user_data.model_dump(exclude_unset=True)
            current_user = self.user_service.get_user(user_id)
            if (
                update_dict.get("notifications_enabled")
                and not current_user.ntfy_topic
                and "ntfy_topic" not in update_dict
            ):
                update_dict["ntfy_topic"] = f"pf-app-{uuid.uuid4()}"
            update_data = UserUpdate.model_validate(update_dict)
        else:
            update_data = user_data

        return self.user_service.update_user(user_id, update_data)


def provide(session: Session) -> UpdateUserUseCase:
    """Provide an instance of UpdateUserUseCase.

    Args:
        session: The database session to use.

    Returns:
        UpdateUserUseCase: A new instance with the user service
    """
    return UpdateUserUseCase(provide_user_service(session))
