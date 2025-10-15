"""Card statement service implementation."""

import uuid
from functools import lru_cache
from typing import Any

from app.domains.card_statements.domain.models import (
    CardStatementCreate,
    CardStatementPublic,
    CardStatementsPublic,
    CardStatementUpdate,
)
from app.domains.card_statements.repository import provide as provide_repository
from app.domains.card_statements.repository.card_statement_repository import (
    CardStatementRepository,
)


class CardStatementService:
    """Service for card statements."""

    def __init__(self, repository: CardStatementRepository):
        """Initialize the service with a repository."""
        self.repository = repository

    def create_statement(
        self, statement_data: CardStatementCreate
    ) -> CardStatementPublic:
        """Create a new card statement."""
        statement = self.repository.create(statement_data)
        return CardStatementPublic.model_validate(statement)

    def get_statement(self, statement_id: uuid.UUID) -> CardStatementPublic:
        """Get a card statement by ID."""
        statement = self.repository.get_by_id(statement_id)
        return CardStatementPublic.model_validate(statement)

    def list_statements(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> CardStatementsPublic:
        """List card statements with pagination and filtering."""
        statements = self.repository.list(skip=skip, limit=limit, filters=filters)
        count = self.repository.count(filters=filters)

        return CardStatementsPublic(
            data=[CardStatementPublic.model_validate(s) for s in statements],
            count=count,
        )

    def update_statement(
        self, statement_id: uuid.UUID, statement_data: CardStatementUpdate
    ) -> CardStatementPublic:
        """Update a card statement."""
        statement = self.repository.update(statement_id, statement_data)
        return CardStatementPublic.model_validate(statement)

    def delete_statement(self, statement_id: uuid.UUID) -> None:
        """Delete a card statement."""
        self.repository.delete(statement_id)


@lru_cache
def provide() -> CardStatementService:
    """Provide an instance of CardStatementService."""
    return CardStatementService(provide_repository())
