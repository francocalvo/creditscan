"""Usecase for updating user password."""

import uuid

from app.core.security import verify_password
from app.domains.users.domain.errors import (
    InvalidCredentialsError,
    InvalidUserDataError,
)
from app.domains.users.domain.models import UpdatePassword, UserUpdate
from app.domains.users.service import UserService
from app.domains.users.service import provide as provide_user_service


class UpdatePasswordUseCase:
    """Usecase for updating user password."""

    def __init__(self, user_service: UserService) -> None:
        """Initialize the usecase with a user service.

        Args:
            user_service: Service for handling user operations
        """
        self.user_service = user_service

    def execute(self, user_id: uuid.UUID, password_data: UpdatePassword) -> None:
        """Execute the usecase to update user password.

        Args:
            user_id: The user ID
            password_data: Password update data

        Raises:
            InvalidCredentialsError: If current password is incorrect
            InvalidUserDataError: If new password is same as current
        """
        # Get the user (includes hashed password)
        user = self.user_service.user_repository.get_by_id(user_id)

        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect password")

        # Check if new password is different
        if password_data.current_password == password_data.new_password:
            raise InvalidUserDataError(
                "New password cannot be the same as the current one"
            )

        # Update password
        user_update = UserUpdate(password=password_data.new_password)
        self.user_service.update_user(user_id, user_update)


def provide() -> UpdatePasswordUseCase:
    """Provide an instance of UpdatePasswordUseCase.

    Returns:
        UpdatePasswordUseCase: A new instance with the user service
    """
    return UpdatePasswordUseCase(provide_user_service())
