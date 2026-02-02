"""Usecase for deleting a card statement."""

import uuid

from sqlmodel import Session

from app.domains.card_statements.service import CardStatementService
from app.domains.card_statements.service import provide as provide_service


class DeleteCardStatementUseCase:
    """Usecase for deleting a card statement."""

    def __init__(self, service: CardStatementService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, statement_id: uuid.UUID) -> None:
        """Execute the usecase to delete a card statement.

        Args:
            statement_id: The ID of the statement to delete
        """
        self.service.delete_statement(statement_id)


def provide(session: Session) -> DeleteCardStatementUseCase:
    """Provide an instance of DeleteCardStatementUseCase.

    Args:
        session: The database session to use.
    """
    return DeleteCardStatementUseCase(provide_service(session))
