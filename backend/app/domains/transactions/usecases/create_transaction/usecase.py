"""Usecase for creating a transaction."""

from app.domains.transactions.domain.models import (
    TransactionCreate,
    TransactionPublic,
)
from app.domains.transactions.service import TransactionService
from app.domains.transactions.service import provide as provide_service


class CreateTransactionUseCase:
    """Usecase for creating a transaction."""

    def __init__(self, service: TransactionService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, transaction_data: TransactionCreate) -> TransactionPublic:
        """Execute the usecase to create a transaction.

        Args:
            transaction_data: The transaction data to create

        Returns:
            TransactionPublic: The created transaction
        """
        return self.service.create_transaction(transaction_data)


def provide() -> CreateTransactionUseCase:
    """Provide an instance of CreateTransactionUseCase."""
    return CreateTransactionUseCase(provide_service())
