"""Usecase for updating a card statement."""

import uuid

from app.domains.card_statements.domain.models import (
    CardStatementPublic,
    CardStatementUpdate,
)
from app.domains.card_statements.service import CardStatementService
from app.domains.card_statements.service import provide as provide_service


class UpdateCardStatementUseCase:
    """Usecase for updating a card statement."""

    def __init__(self, service: CardStatementService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self, statement_id: uuid.UUID, statement_data: CardStatementUpdate
    ) -> CardStatementPublic:
        """Execute the usecase to update a card statement.

        Args:
            statement_id: The ID of the statement to update
            statement_data: The updated statement data

        Returns:
            CardStatementPublic: The updated statement
        """
        return self.service.update_statement(statement_id, statement_data)


def provide() -> UpdateCardStatementUseCase:
    """Provide an instance of UpdateCardStatementUseCase."""
    return UpdateCardStatementUseCase(provide_service())
