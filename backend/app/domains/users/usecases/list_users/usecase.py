"""Usecase for listing users with pagination."""

from app.domains.users.domain.models import UsersPublic
from app.domains.users.service import UserService
from app.domains.users.service import provide as provide_user_service


class ListUsersUseCase:
    """Usecase for listing users with pagination."""

    def __init__(self, user_service: UserService) -> None:
        """Initialize the usecase with a user service.

        Args:
            user_service: Service for handling user operations
        """
        self.user_service = user_service

    def execute(self, skip: int = 0, limit: int = 100) -> UsersPublic:
        """Execute the usecase to list users with pagination.

        Args:
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            UsersPublic: Paginated users data
        """
        return self.user_service.list_users(skip=skip, limit=limit)


def provide() -> ListUsersUseCase:
    """Provide an instance of ListUsersUseCase.

    Returns:
        ListUsersUseCase: A new instance with the user service
    """
    return ListUsersUseCase(provide_user_service())
