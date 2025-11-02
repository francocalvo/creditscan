"""Usecase for adding a tag to a transaction."""

from app.domains.transaction_tags.domain.models import (
    TransactionTagCreate,
    TransactionTagPublic,
)
from app.domains.transaction_tags.service import TransactionTagService
from app.domains.transaction_tags.service import (
    provide as provide_service,
)


class AddTagToTransactionUseCase:
    """Usecase for adding a tag to a transaction."""

    def __init__(self, service: TransactionTagService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self, transaction_tag_data: TransactionTagCreate
    ) -> TransactionTagPublic:
        """Execute the usecase to add a tag to a transaction.

        Args:
            transaction_tag_data: The transaction tag data

        Returns:
            TransactionTagPublic: The created transaction tag relationship
        """
        return self.service.add_tag_to_transaction(transaction_tag_data)


def provide() -> AddTagToTransactionUseCase:
    """Provide an instance of AddTagToTransactionUseCase."""
    return AddTagToTransactionUseCase(provide_service())
