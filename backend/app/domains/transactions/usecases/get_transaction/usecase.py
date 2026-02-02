"""Usecase for getting a transaction by ID."""

import uuid

from sqlmodel import Session

from app.domains.transactions.domain.models import TransactionPublic
from app.domains.transactions.service import TransactionService
from app.domains.transactions.service import provide as provide_service


class GetTransactionUseCase:
    """Usecase for getting a transaction by ID."""

    def __init__(self, service: TransactionService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, transaction_id: uuid.UUID) -> TransactionPublic:
        """Execute the usecase to get a transaction.

        Args:
            transaction_id: The ID of the transaction to retrieve

        Returns:
            TransactionPublic: The transaction data
        """
        return self.service.get_transaction(transaction_id)


def provide(session: Session) -> GetTransactionUseCase:
    """Provide an instance of GetTransactionUseCase.

    Args:
        session: The database session to use.
    """
    return GetTransactionUseCase(provide_service(session))
