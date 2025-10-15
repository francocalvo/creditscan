"""Card statement repository implementation."""

import uuid
from functools import lru_cache
from typing import Any

from sqlmodel import Session, func, select

from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.domain.models import (
    CardStatement,
    CardStatementCreate,
    CardStatementUpdate,
)
from app.pkgs.database import get_db_session


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
        """List card statements with pagination and filtering."""
        query = select(CardStatement)

        if filters:
            for field, value in filters.items():
                if hasattr(CardStatement, field):
                    query = query.where(getattr(CardStatement, field) == value)

        result = self.db_session.exec(query.offset(skip).limit(limit))
        return list(result)

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count card statements with optional filtering."""
        query = select(CardStatement)

        if filters:
            for field, value in filters.items():
                if hasattr(CardStatement, field):
                    query = query.where(getattr(CardStatement, field) == value)

        count_q = (
            query.with_only_columns(func.count())
            .order_by(None)
            .select_from(query.get_final_froms()[0])
        )

        result = self.db_session.exec(count_q)
        for count in result:
            return count  # type: ignore
        return 0

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


@lru_cache
def provide() -> CardStatementRepository:
    """Provide an instance of CardStatementRepository."""
    return CardStatementRepository(get_db_session())
