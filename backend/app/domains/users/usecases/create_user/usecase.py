"""Usecase for creating a new user."""

from app.core.config import settings
from app.domains.users.domain.errors import DuplicateUserError
from app.domains.users.domain.models import UserCreate, UserPublic
from app.domains.users.service import UserService
from app.domains.users.service import provide as provide_user_service
from app.utils import generate_new_account_email, send_email


class CreateUserUseCase:
    """Usecase for creating a new user."""

    def __init__(self, user_service: UserService) -> None:
        """Initialize the usecase with a user service.

        Args:
            user_service: Service for handling user operations
        """
        self.user_service = user_service

    def execute(
        self, user_data: UserCreate, send_welcome_email: bool = True
    ) -> UserPublic:
        """Execute the usecase to create a new user.

        Args:
            user_data: User creation data
            send_welcome_email: Whether to send welcome email

        Returns:
            UserPublic: The created user

        Raises:
            DuplicateUserError: If user with email already exists
        """
        # Check if user already exists
        existing_user = self.user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise DuplicateUserError(
                "The user with this email already exists in the system."
            )

        # Create the user
        user = self.user_service.create_user(user_data)

        # Send welcome email if enabled
        if send_welcome_email and settings.emails_enabled and user_data.email:
            email_data = generate_new_account_email(
                email_to=user_data.email,
                username=user_data.email,
                password=user_data.password,
            )
            send_email(
                email_to=user_data.email,
                subject=email_data.subject,
                html_content=email_data.html_content,
            )

        return user


def provide() -> CreateUserUseCase:
    """Provide an instance of CreateUserUseCase.

    Returns:
        CreateUserUseCase: A new instance with the user service
    """
    return CreateUserUseCase(provide_user_service())
