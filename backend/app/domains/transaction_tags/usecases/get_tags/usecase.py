"""Usecase for getting tags for a transaction."""

import uuid

from app.domains.transaction_tags.domain.models import TransactionTagPublic
from app.domains.transaction_tags.service import TransactionTagService
from app.domains.transaction_tags.service.transaction_tag_service import (
    provide as provide_service,
)


class GetTransactionTagsUseCase:
    """Usecase for getting tags for a transaction."""

    def __init__(self, service: TransactionTagService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, transaction_id: uuid.UUID) -> list[TransactionTagPublic]:
        """Execute the usecase to get tags for a transaction.

        Args:
            transaction_id: The ID of the transaction

        Returns:
            list[TransactionTagPublic]: List of transaction tag relationships
        """
        return self.service.get_transaction_tags(transaction_id)


def provide() -> GetTransactionTagsUseCase:
    """Provide an instance of GetTransactionTagsUseCase."""
    return GetTransactionTagsUseCase(provide_service())
