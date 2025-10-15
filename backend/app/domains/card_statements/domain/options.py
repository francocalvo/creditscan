"""Search options for card statements domain."""

import uuid
from datetime import date
from enum import Enum

from app.constants import DEFAULT_PAGINATION_LIMIT


class SortOrder(Enum):
    """Enumeration for sorting order."""

    ASC = "asc"
    DESC = "desc"


class SearchFilters:
    """Options for searching card statements."""

    user_id: uuid.UUID | None = None
    card_last4: str | None = None
    card_brand: str | None = None
    from_date: date | None = None
    to_date: date | None = None

    def __init__(
        self,
        user_id: uuid.UUID | None = None,
        card_last4: str | None = None,
        card_brand: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        self.user_id = user_id
        self.card_last4 = card_last4
        self.card_brand = card_brand
        self.from_date = from_date
        self.to_date = to_date


class SearchPagination:
    """Options for paginating search results."""

    skip: int = 0
    limit: int = 50

    def __init__(self, skip: int = 0, limit: int = DEFAULT_PAGINATION_LIMIT):
        self.skip = skip
        self.limit = limit if limit > 0 else DEFAULT_PAGINATION_LIMIT


class SearchSorting:
    """Options for sorting search results."""

    field: str = "close_date"
    order: SortOrder = SortOrder.DESC

    def __init__(self, field: str = "close_date", order: SortOrder = SortOrder.DESC):
        self.field = field
        self.order = order


class SearchOptions:
    """Options for searching card statements."""

    filters: SearchFilters
    pagination: SearchPagination
    sorting: SearchSorting

    def __init__(self):
        self.filters = SearchFilters()
        self.pagination = SearchPagination()
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
