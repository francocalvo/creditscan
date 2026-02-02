"""Use case for searching users by email."""

from sqlmodel import Session

from app.domains.users.domain.models import UsersPublic
from app.domains.users.domain.options import (
    SearchFilters,
    SearchOptions,
    SearchPagination,
    SearchSorting,
    SortOrder,
)
from app.domains.users.service import UserService
from app.domains.users.service import provide as provide_service


class SearchUsersUseCase:
    """Use case for searching users with advanced filtering.

    This use case provides a flexible search interface that supports:
    - Email search (partial matching)
    - Full name search (partial matching)
    - Active/inactive filtering
    - Superuser filtering
    - Custom sorting
    - Pagination
    """

    def __init__(self, service: UserService) -> None:
        """Initialize the use case with a service.

        Args:
            service: The user service instance
        """
        self.service = service

    def execute(
        self,
        email: str | None = None,
        full_name: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = "email",
        sort_order: SortOrder = SortOrder.ASC,
    ) -> UsersPublic:
        """Execute the search users use case.

        Args:
            email: Optional email filter (partial match, e.g., "john" matches "john@example.com")
            full_name: Optional full name filter (partial match)
            is_active: Optional active status filter
            is_superuser: Optional superuser status filter
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            sort_field: Field to sort by (default: "email")
            sort_order: Sort order (ASC or DESC, default: ASC)

        Returns:
            UsersPublic: Paginated search results with total count

        Example:
            Search for active users with email containing "john":
            >>> usecase = SearchUsersUseCase(user_service)
            >>> results = usecase.execute(email="john", is_active=True, limit=10)

            Search all superusers sorted by email descending:
            >>> results = usecase.execute(
            ...     is_superuser=True,
            ...     sort_field="email",
            ...     sort_order=SortOrder.DESC
            ... )
        """
        # Build search options
        search_options = SearchOptions()

        # Configure filters
        filters = SearchFilters(
            email=email,
            full_name=full_name,
            is_active=is_active,
            is_superuser=is_superuser,
        )
        search_options.with_filters(filters)

        # Configure pagination
        pagination = SearchPagination(skip=skip, limit=limit)
        search_options.with_pagination(pagination)

        # Configure sorting
        sorting = SearchSorting(field=sort_field, order=sort_order)
        search_options.with_sorting(sorting)

        # Execute the search
        return self.service.search(search_options)


def provide(session: Session) -> SearchUsersUseCase:
    """Provide an instance of SearchUsersUseCase.

    Args:
        session: The database session to use.

    Returns:
        SearchUsersUseCase: An instance of the use case with dependencies
    """
    return SearchUsersUseCase(provide_service(session))
