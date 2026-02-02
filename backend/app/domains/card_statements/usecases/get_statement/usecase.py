"""Usecase for getting a card statement by ID."""

import uuid

from sqlmodel import Session

from app.domains.card_statements.domain.models import CardStatementPublic
from app.domains.card_statements.service import CardStatementService
from app.domains.card_statements.service import provide as provide_service


class GetCardStatementUseCase:
    """Usecase for getting a card statement by ID."""

    def __init__(self, service: CardStatementService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, statement_id: uuid.UUID) -> CardStatementPublic:
        """Execute the usecase to get a card statement.

        Args:
            statement_id: The ID of the statement to retrieve

        Returns:
            CardStatementPublic: The statement data
        """
        return self.service.get_statement(statement_id)


def provide(session: Session) -> GetCardStatementUseCase:
    """Provide an instance of GetCardStatementUseCase.

    Args:
        session: The database session to use.
    """
    return GetCardStatementUseCase(provide_service(session))
