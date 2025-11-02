"""Transaction tag service implementation."""

import uuid
from functools import lru_cache

from app.domains.transaction_tags.domain.models import (
    TransactionTagCreate,
    TransactionTagPublic,
)
from app.domains.transaction_tags.repository.transaction_tag_repository import (
    TransactionTagRepository,
)
from app.domains.transaction_tags.repository.transaction_tag_repository import (
    provide as provide_repository,
)


class TransactionTagService:
    """Service for transaction tags."""

    def __init__(self, repository: TransactionTagRepository):
        """Initialize the service with a repository."""
        self.repository = repository

    def add_tag_to_transaction(
        self, transaction_tag_data: TransactionTagCreate
    ) -> TransactionTagPublic:
        """Add a tag to a transaction."""
        transaction_tag = self.repository.create(transaction_tag_data)
        return TransactionTagPublic.model_validate(transaction_tag)

    def get_transaction_tags(
        self, transaction_id: uuid.UUID
    ) -> list[TransactionTagPublic]:
        """Get all tags for a transaction."""
        transaction_tags = self.repository.list_by_transaction(transaction_id)
        return [TransactionTagPublic.model_validate(tt) for tt in transaction_tags]

    def get_tag_transactions(self, tag_id: uuid.UUID) -> list[TransactionTagPublic]:
        """Get all transactions for a tag."""
        transaction_tags = self.repository.list_by_tag(tag_id)
        return [TransactionTagPublic.model_validate(tt) for tt in transaction_tags]

    def remove_tag_from_transaction(
        self, transaction_id: uuid.UUID, tag_id: uuid.UUID
    ) -> None:
        """Remove a tag from a transaction."""
        self.repository.delete(transaction_id, tag_id)


@lru_cache
def provide() -> TransactionTagService:
    """Provide an instance of TransactionTagService."""
    return TransactionTagService(provide_repository())
