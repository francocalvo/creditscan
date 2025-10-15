"""Usecase for creating a card statement."""

from app.domains.card_statements.domain.models import (
    CardStatementCreate,
    CardStatementPublic,
)
from app.domains.card_statements.service import CardStatementService
from app.domains.card_statements.service import provide as provide_service


class CreateCardStatementUseCase:
    """Usecase for creating a card statement."""

    def __init__(self, service: CardStatementService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, statement_data: CardStatementCreate) -> CardStatementPublic:
        """Execute the usecase to create a card statement.

        Args:
            statement_data: The card statement data to create

        Returns:
            CardStatementPublic: The created statement
        """
        return self.service.create_statement(statement_data)


def provide() -> CreateCardStatementUseCase:
    """Provide an instance of CreateCardStatementUseCase."""
    return CreateCardStatementUseCase(provide_service())
