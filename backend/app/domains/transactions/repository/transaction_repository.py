"""Transaction repository implementation."""

import builtins
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

    def get_by_id_for_user(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID
    ) -> Transaction | None:
        """Get a transaction by ID, verifying it belongs to the user.

        Args:
            transaction_id: The ID of the transaction to fetch.
            user_id: The ID of the user who should own the transaction.

        Returns:
            The transaction if it exists and belongs to the user, None otherwise.
        """
        # Join: Transaction → CardStatement → CreditCard → user_id
        from app.domains.card_statements.domain.models import CardStatement
        from app.domains.credit_cards.domain.models import CreditCard

        query = (
            select(Transaction)
            .join(CardStatement, Transaction.statement_id == CardStatement.id)
            .join(CreditCard, CardStatement.card_id == CreditCard.id)
            .where(Transaction.id == transaction_id)
            .where(CreditCard.user_id == user_id)
        )

        result = self.db_session.exec(query).first()
        return result

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

    def list_for_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> builtins.list[Transaction]:
        """List transactions belonging to a specific user.

        Args:
            user_id: The ID of the user to fetch transactions for.
            skip: Number of records to skip (for pagination).
            limit: Maximum number of records to return.
            filters: Additional filters to apply (e.g., statement_id).

        Returns:
            List of transactions belonging to the user.
        """
        # Join: Transaction → CardStatement → CreditCard → user_id
        from app.domains.card_statements.domain.models import CardStatement
        from app.domains.credit_cards.domain.models import CreditCard

        query = (
            select(Transaction)
            .join(CardStatement, Transaction.statement_id == CardStatement.id)
            .join(CreditCard, CardStatement.card_id == CreditCard.id)
            .where(CreditCard.user_id == user_id)
        )

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
