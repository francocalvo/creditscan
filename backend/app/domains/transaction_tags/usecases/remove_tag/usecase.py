"""Usecase for removing a tag from a transaction."""

import uuid

from app.domains.transaction_tags.service import TransactionTagService
from app.domains.transaction_tags.service import (
    provide as provide_service,
)


class RemoveTagFromTransactionUseCase:
    """Usecase for removing a tag from a transaction."""

    def __init__(self, service: TransactionTagService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, transaction_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        """Execute the usecase to remove a tag from a transaction.

        Args:
            transaction_id: The ID of the transaction
            tag_id: The ID of the tag
        """
        self.service.remove_tag_from_transaction(transaction_id, tag_id)


def provide() -> RemoveTagFromTransactionUseCase:
    """Provide an instance of RemoveTagFromTransactionUseCase."""
    return RemoveTagFromTransactionUseCase(provide_service())
