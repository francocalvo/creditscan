"""Transaction repository implementation."""

import uuid
from typing import Any

from sqlmodel import Session, func, select

from app.domains.transactions.domain.errors import TransactionNotFoundError
from app.domains.transactions.domain.models import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
)


class TransactionRepository:
    """Repository for transactions."""

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db_session = db_session

    def create(self, transaction_data: TransactionCreate) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction.model_validate(transaction_data)
        self.db_session.add(transaction)
        self.db_session.commit()
        self.db_session.refresh(transaction)
        return transaction

    def get_by_id(self, transaction_id: uuid.UUID) -> Transaction:
        """Get a transaction by ID."""
        transaction = self.db_session.get(Transaction, transaction_id)
        if not transaction:
            raise TransactionNotFoundError(
                f"Transaction with ID {transaction_id} not found"
            )
        return transaction

    def list(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[Transaction]:
        """List transactions with pagination and filtering."""
        query = select(Transaction)

        if filters:
            for field, value in filters.items():
                if hasattr(Transaction, field):
                    query = query.where(getattr(Transaction, field) == value)

        result = self.db_session.exec(query.offset(skip).limit(limit))
        return list(result)

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count transactions with optional filtering."""
        query = select(Transaction)

        if filters:
            for field, value in filters.items():
                if hasattr(Transaction, field):
                    query = query.where(getattr(Transaction, field) == value)

        count_q = (
            query.with_only_columns(func.count())
            .order_by(None)
            .select_from(query.get_final_froms()[0])
        )

        result = self.db_session.exec(count_q)  # type: ignore
        for count in result:  # type: ignore
            return count  # type: ignore
        return 0

    def update(
        self,
        transaction_id: uuid.UUID,
        transaction_data: TransactionUpdate,
    ) -> Transaction:
        """Update a transaction."""
        transaction = self.get_by_id(transaction_id)

        update_dict = transaction_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(transaction, field, value)

        self.db_session.add(transaction)
        self.db_session.commit()
        self.db_session.refresh(transaction)
        return transaction

    def delete(self, transaction_id: uuid.UUID) -> None:
        """Delete a transaction."""
        transaction = self.get_by_id(transaction_id)
        self.db_session.delete(transaction)
        self.db_session.commit()


def provide(session: Session) -> TransactionRepository:
    """Provide an instance of TransactionRepository.

    Args:
        session: The database session to use.

    Returns:
        TransactionRepository: An instance of TransactionRepository with the given session.
    """
    return TransactionRepository(session)
