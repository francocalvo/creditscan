"""Usecase for user self-registration."""

from app.domains.users.domain.errors import DuplicateUserError
from app.domains.users.domain.models import UserCreate, UserPublic, UserRegister
from app.domains.users.service import UserService
from app.domains.users.service import provide as provide_user_service


class RegisterUserUseCase:
    """Usecase for user self-registration without authentication."""

    def __init__(self, user_service: UserService) -> None:
        """Initialize the usecase with a user service.

        Args:
            user_service: Service for handling user operations
        """
        self.user_service = user_service

    def execute(self, user_data: UserRegister) -> UserPublic:
        """Execute the usecase to register a new user.

        Args:
            user_data: User registration data

        Returns:
            UserPublic: The registered user

        Raises:
            DuplicateUserError: If user with email already exists
        """
        # Check if user already exists
        existing_user = self.user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise DuplicateUserError(
                "The user with this email already exists in the system"
            )

        # Convert to UserCreate and create the user
        user_create = UserCreate.model_validate(user_data)
        return self.user_service.create_user(user_create)


def provide() -> RegisterUserUseCase:
    """Provide an instance of RegisterUserUseCase.

    Returns:
        RegisterUserUseCase: A new instance with the user service
    """
    return RegisterUserUseCase(provide_user_service())
