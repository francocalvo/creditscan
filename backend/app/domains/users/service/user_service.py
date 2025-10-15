"""User service implementation."""

import uuid
from functools import lru_cache
from typing import Any

from app.domains.users.domain.models import (
    UserCreate,
    UserPublic,
    UsersPublic,
    UserUpdate,
)
from app.domains.users.domain.options import SearchOptions
from app.domains.users.repository import provide as provide_repository
from app.domains.users.repository.user_repository import UserRepository


class UserService:
    """Service for users."""

    def __init__(self, user_repository: UserRepository):
        """Initialize the service with a repository."""
        self.user_repository = user_repository

    def create_user(self, user_data: UserCreate) -> UserPublic:
        """Create a new user.

        Args:
            user_data: User creation data

        Returns:
            UserPublic: The created user
        """
        user = self.user_repository.create(user_data)
        return UserPublic.model_validate(user)

    def get_user(self, user_id: uuid.UUID) -> UserPublic:
        """Get a user by ID.

        Args:
            user_id: The user ID

        Returns:
            UserPublic: The user

        Raises:
            UserNotFoundError: If user is not found
        """
        user = self.user_repository.get_by_id(user_id)
        return UserPublic.model_validate(user)

    def get_user_by_email(self, email: str) -> UserPublic | None:
        """Get a user by email.

        Args:
            email: The user email

        Returns:
            UserPublic | None: The user if found, None otherwise
        """
        user = self.user_repository.get_by_email(email)
        if user:
            return UserPublic.model_validate(user)
        return None

    def list_users(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> UsersPublic:
        """List users with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters to apply

        Returns:
            UsersPublic: Paginated users data
        """
        users = self.user_repository.list(skip=skip, limit=limit, filters=filters)
        count = self.user_repository.count(filters=filters)

        return UsersPublic(
            data=[UserPublic.model_validate(user) for user in users],
            count=count,
        )

    def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> UserPublic:
        """Update a user.

        Args:
            user_id: The user ID
            user_data: User update data

        Returns:
            UserPublic: The updated user

        Raises:
            UserNotFoundError: If user is not found
        """
        user = self.user_repository.update(user_id, user_data)
        return UserPublic.model_validate(user)

    def delete_user(self, user_id: uuid.UUID) -> None:
        """Delete a user.

        Args:
            user_id: The user ID

        Raises:
            UserNotFoundError: If user is not found
        """
        self.user_repository.delete(user_id)

    def search(self, search_options: SearchOptions) -> UsersPublic:
        """Search users with advanced filtering options.

        This method provides comprehensive search capabilities:
        - Partial email matching (e.g., "john" matches "john@example.com")
        - Partial full name matching (e.g., "Smith" matches "John Smith")
        - Active/inactive status filtering
        - Superuser status filtering
        - Sorting by any field (email, full_name, etc.)
        - Pagination with skip and limit

        Args:
            search_options: Search options including filters, pagination, and sorting

        Returns:
            UsersPublic: Paginated search results with total count

        Example:
            >>> from app.domains.users.domain.options import SearchOptions, SearchFilters
            >>> options = SearchOptions()
            >>> options.with_filters(SearchFilters(email="john", is_active=True))
            >>> results = service.search(options)
        """
        users = self.user_repository.search(search_options)
        count = self.user_repository.count_by_search_options(search_options)

        return UsersPublic(
            data=[UserPublic.model_validate(user) for user in users],
            count=count,
        )

    def authenticate(self, email: str, password: str) -> UserPublic | None:
        """Authenticate a user by email and password.

        Args:
            email: The user email
            password: The user password

        Returns:
            UserPublic | None: The user if authentication successful, None otherwise
        """
        user = self.user_repository.authenticate(email, password)
        if user:
            return UserPublic.model_validate(user)
        return None


@lru_cache
def provide() -> UserService:
    """Provide an instance of UserService.

    Returns:
        UserService: An instance of UserService with a repository.
    """
    return UserService(provide_repository())
