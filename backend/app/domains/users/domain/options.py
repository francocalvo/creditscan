"""Search options for users domain."""

from enum import Enum

from app.constants import DEFAULT_PAGINATION_LIMIT


class SortOrder(Enum):
    """Enumeration for sorting order."""

    ASC = "asc"
    DESC = "desc"


class SearchFilters:
    """Options for searching users."""

    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None

    def __init__(
        self,
        email: str | None = None,
        full_name: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
    ):
        self.email = email if email else None
        self.full_name = full_name if full_name else None
        self.is_active = is_active
        self.is_superuser = is_superuser


class SearchPagination:
    """Options for paginating search results."""

    skip: int = 0
    limit: int = 50

    def __init__(self, skip: int = 0, limit: int = DEFAULT_PAGINATION_LIMIT):
        self.skip = skip
        self.limit = limit if limit > 0 else DEFAULT_PAGINATION_LIMIT


class SearchSorting:
    """Options for sorting search results."""

    field: str = "email"
    order: SortOrder = SortOrder.ASC

    def __init__(self, field: str = "email", order: SortOrder = SortOrder.ASC):
        self.field = field
        self.order = order


class SearchOptions:
    """Options for searching users."""

    filters: SearchFilters
    pagination: SearchPagination
    sorting: SearchSorting

    def __init__(self):
        self.filters = SearchFilters()
        self.pagination = SearchPagination(skip=0, limit=DEFAULT_PAGINATION_LIMIT)
        self.sorting = SearchSorting()

    def with_filters(self, filters: SearchFilters) -> "SearchOptions":
        """Set filters and return self for method chaining."""
        self.filters = filters
        return self

    def with_pagination(self, pagination: SearchPagination) -> "SearchOptions":
        """Set pagination and return self for method chaining."""
        self.pagination = pagination
        return self

    def with_sorting(self, sorting: SearchSorting) -> "SearchOptions":
        """Set sorting and return self for method chaining."""
        self.sorting = sorting
        return self
