"""Usecase for listing transactions."""

import uuid

from app.domains.transactions.domain.models import TransactionsPublic
from app.domains.transactions.service import TransactionService
from app.domains.transactions.service import provide as provide_service


class ListTransactionsUseCase:
    """Usecase for listing transactions with pagination."""

    def __init__(self, service: TransactionService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        statement_id: uuid.UUID | None = None,
    ) -> TransactionsPublic:
        """Execute the usecase to list transactions.

        Args:
            skip: Number of records to skip
            limit: Number of records to return
            statement_id: Optional filter by card statement ID

        Returns:
            TransactionsPublic: Paginated transactions data
        """
        filters = {}
        if statement_id:
            filters["statement_id"] = statement_id

        return self.service.list_transactions(skip=skip, limit=limit, filters=filters)


def provide() -> ListTransactionsUseCase:
    """Provide an instance of ListTransactionsUseCase."""
    return ListTransactionsUseCase(provide_service())
