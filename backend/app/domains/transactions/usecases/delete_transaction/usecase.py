"""Usecase for deleting a transaction."""

import uuid

from sqlmodel import Session

from app.domains.transactions.service import TransactionService
from app.domains.transactions.service import provide as provide_service


class DeleteTransactionUseCase:
    """Usecase for deleting a transaction."""

    def __init__(self, service: TransactionService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, transaction_id: uuid.UUID) -> None:
        """Execute the usecase to delete a transaction.

        Args:
            transaction_id: The ID of the transaction to delete
        """
        self.service.delete_transaction(transaction_id)


def provide(session: Session) -> DeleteTransactionUseCase:
    """Provide an instance of DeleteTransactionUseCase.

    Args:
        session: The database session to use.
    """
    return DeleteTransactionUseCase(provide_service(session))
