"""Usecase for updating a transaction."""

import uuid

from app.domains.transactions.domain.models import (
    TransactionPublic,
    TransactionUpdate,
)
from app.domains.transactions.service import TransactionService
from app.domains.transactions.service import provide as provide_service


class UpdateTransactionUseCase:
    """Usecase for updating a transaction."""

    def __init__(self, service: TransactionService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self,
        transaction_id: uuid.UUID,
        transaction_data: TransactionUpdate,
    ) -> TransactionPublic:
        """Execute the usecase to update a transaction.

        Args:
            transaction_id: The ID of the transaction to update
            transaction_data: The transaction data to update

        Returns:
            TransactionPublic: The updated transaction
        """
        return self.service.update_transaction(transaction_id, transaction_data)


def provide() -> UpdateTransactionUseCase:
    """Provide an instance of UpdateTransactionUseCase."""
    return UpdateTransactionUseCase(provide_service())
