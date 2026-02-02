"""Card statement repository implementation."""

import uuid
from typing import Any

from sqlmodel import Session, func, select

from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.domain.models import (
    CardStatement,
    CardStatementCreate,
    CardStatementUpdate,
)
from app.domains.credit_cards.domain.models import CreditCard


class CardStatementRepository:
    """Repository for card statements."""

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db_session = db_session

    def create(self, statement_data: CardStatementCreate) -> CardStatement:
        """Create a new card statement."""
        statement = CardStatement.model_validate(statement_data)
        self.db_session.add(statement)
        self.db_session.commit()
        self.db_session.refresh(statement)
        return statement

    def get_by_id(self, statement_id: uuid.UUID) -> CardStatement:
        """Get a card statement by ID."""
        statement = self.db_session.get(CardStatement, statement_id)
        if not statement:
            raise CardStatementNotFoundError(
                f"Card statement with ID {statement_id} not found"
            )
        return statement

    def list(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[CardStatement]:
        """List card statements with pagination and filtering.

        Supports filtering by user_id through the credit_card relationship.
        """
        query = select(CardStatement)

        # Check if we need to join with credit_card for user_id filtering
        needs_join = filters and "user_id" in filters

        if needs_join:
            query = query.join(CreditCard, CardStatement.card_id == CreditCard.id)

        if filters:
            for field, value in filters.items():
                if field == "user_id":
                    # Filter by user_id through the credit_card join
                    query = query.where(CreditCard.user_id == value)
                elif hasattr(CardStatement, field):
                    query = query.where(getattr(CardStatement, field) == value)

        result = self.db_session.exec(query.offset(skip).limit(limit))
        return list(result)

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count card statements with optional filtering.

        Supports filtering by user_id through the credit_card relationship.
        """
        # Check if we need to join with credit_card for user_id filtering
        needs_join = filters and "user_id" in filters

        if needs_join:
            # Use select with join for user_id filtering
            query = (
                select(func.count(CardStatement.id))
                .select_from(CardStatement)
                .join(CreditCard, CardStatement.card_id == CreditCard.id)
            )
        else:
            # Simple count without join
            query = select(func.count(CardStatement.id)).select_from(CardStatement)

        if filters:
            for field, value in filters.items():
                if field == "user_id":
                    # Filter by user_id through the credit_card join
                    query = query.where(CreditCard.user_id == value)
                elif hasattr(CardStatement, field):
                    query = query.where(getattr(CardStatement, field) == value)

        result = self.db_session.exec(query)
        return result.one()

    def update(
        self, statement_id: uuid.UUID, statement_data: CardStatementUpdate
    ) -> CardStatement:
        """Update a card statement."""
        statement = self.get_by_id(statement_id)

        update_dict = statement_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(statement, field, value)

        self.db_session.add(statement)
        self.db_session.commit()
        self.db_session.refresh(statement)
        return statement

    def delete(self, statement_id: uuid.UUID) -> None:
        """Delete a card statement."""
        statement = self.get_by_id(statement_id)
        self.db_session.delete(statement)
        self.db_session.commit()


def provide(session: Session) -> CardStatementRepository:
    """Provide an instance of CardStatementRepository.

    Args:
        session: The database session to use.

    Returns:
        CardStatementRepository: An instance of CardStatementRepository with the given session.
    """
    return CardStatementRepository(session)
