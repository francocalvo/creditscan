"""Transaction tag repository implementation."""

import uuid
from functools import lru_cache

from sqlmodel import Session, select

from app.domains.transaction_tags.domain.errors import (
    TransactionTagNotFoundError,
)
from app.domains.transaction_tags.domain.models import (
    TransactionTag,
    TransactionTagCreate,
)
from app.pkgs.database import get_db_session


class TransactionTagRepository:
    """Repository for transaction tags."""

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db_session = db_session

    def create(self, transaction_tag_data: TransactionTagCreate) -> TransactionTag:
        """Create a new transaction tag relationship."""
        transaction_tag = TransactionTag.model_validate(transaction_tag_data)
        self.db_session.add(transaction_tag)
        self.db_session.commit()
        self.db_session.refresh(transaction_tag)
        return transaction_tag

    def get_by_ids(
        self, transaction_id: uuid.UUID, tag_id: uuid.UUID
    ) -> TransactionTag:
        """Get a transaction tag relationship by IDs."""
        query = select(TransactionTag).where(
            TransactionTag.transaction_id == transaction_id,
            TransactionTag.tag_id == tag_id,
        )
        result = self.db_session.exec(query).first()
        if not result:
            raise TransactionTagNotFoundError(
                f"Transaction tag relationship not found for transaction {transaction_id} and tag {tag_id}"
            )
        return result

    def list_by_transaction(self, transaction_id: uuid.UUID) -> list[TransactionTag]:
        """List all tags for a transaction."""
        query = select(TransactionTag).where(
            TransactionTag.transaction_id == transaction_id
        )
        result = self.db_session.exec(query)
        return list(result)

    def list_by_tag(self, tag_id: uuid.UUID) -> list[TransactionTag]:
        """List all transactions for a tag."""
        query = select(TransactionTag).where(TransactionTag.tag_id == tag_id)
        result = self.db_session.exec(query)
        return list(result)

    def delete(self, transaction_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        """Delete a transaction tag relationship."""
        transaction_tag = self.get_by_ids(transaction_id, tag_id)
        self.db_session.delete(transaction_tag)
        self.db_session.commit()


@lru_cache
def provide() -> TransactionTagRepository:
    """Provide an instance of TransactionTagRepository."""
    return TransactionTagRepository(get_db_session())
