"""Transaction service implementation."""

import uuid
from functools import lru_cache
from typing import Any

from app.domains.transactions.domain.models import (
    TransactionCreate,
    TransactionPublic,
    TransactionsPublic,
    TransactionUpdate,
)
from app.domains.transactions.repository import provide as provide_repository
from app.domains.transactions.repository.transaction_repository import (
    TransactionRepository,
)


class TransactionService:
    """Service for transactions."""

    def __init__(self, repository: TransactionRepository):
        """Initialize the service with a repository."""
        self.repository = repository

    def create_transaction(
        self, transaction_data: TransactionCreate
    ) -> TransactionPublic:
        """Create a new transaction."""
        transaction = self.repository.create(transaction_data)
        return TransactionPublic.model_validate(transaction)

    def get_transaction(self, transaction_id: uuid.UUID) -> TransactionPublic:
        """Get a transaction by ID."""
        transaction = self.repository.get_by_id(transaction_id)
        return TransactionPublic.model_validate(transaction)

    def list_transactions(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> TransactionsPublic:
        """List transactions with pagination and filtering."""
        transactions = self.repository.list(skip=skip, limit=limit, filters=filters)
        count = self.repository.count(filters=filters)

        return TransactionsPublic(
            data=[TransactionPublic.model_validate(t) for t in transactions],
            count=count,
        )

    def update_transaction(
        self,
        transaction_id: uuid.UUID,
        transaction_data: TransactionUpdate,
    ) -> TransactionPublic:
        """Update a transaction."""
        transaction = self.repository.update(transaction_id, transaction_data)
        return TransactionPublic.model_validate(transaction)

    def delete_transaction(self, transaction_id: uuid.UUID) -> None:
        """Delete a transaction."""
        self.repository.delete(transaction_id)


@lru_cache
def provide() -> TransactionService:
    """Provide an instance of TransactionService."""
    return TransactionService(provide_repository())
